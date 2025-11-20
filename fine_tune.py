
import glob
import os

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.utils.data import Dataset, DataLoader

# =========================================================
# Model definition 
# =========================================================

class AddCoords(nn.Module):
    """Append normalized rank/file channels to a feature map."""
    def forward(self, x):  # x: [B,C,8,8]
        B, C, H, W = x.shape
        yy = torch.linspace(-1, 1, steps=H, device=x.device).view(1, 1, H, 1).expand(B, 1, H, W)
        xx = torch.linspace(-1, 1, steps=W, device=x.device).view(1, 1, 1, W).expand(B, 1, H, W)
        return torch.cat([x, yy, xx], dim=1)  # adds 2 channels


class SE(nn.Module):
    """Squeeze-and-Excitation block for channel attention."""
    def __init__(self, ch, reduction=16):
        super().__init__()
        hidden = max(ch // reduction, 8)
        self.pool = nn.AdaptiveAvgPool2d(1)
        self.fc = nn.Sequential(
            nn.Linear(ch, hidden),
            nn.GELU(),
            nn.Linear(hidden, ch),
            nn.Sigmoid()
        )

    def forward(self, x):
        b, c, _, _ = x.shape
        y = self.pool(x).view(b, c)
        y = self.fc(y).view(b, c, 1, 1)
        return x * y


class DropPath(nn.Module):
    """Stochastic depth. p=0 disables."""
    def __init__(self, p=0.0):
        super().__init__()
        self.p = p

    def forward(self, x):
        if not self.training or self.p == 0.0:
            return x
        keep = 1 - self.p
        mask = torch.empty(x.size(0), 1, 1, 1, device=x.device).bernoulli_(keep) / keep
        return x * mask


class ResBlock(nn.Module):
    def __init__(self, ch: int, drop_path: float = 0.0, use_se: bool = True):
        super().__init__()
        self.conv1 = nn.Conv2d(ch, ch, 3, padding=1, bias=False)
        self.bn1   = nn.BatchNorm2d(ch)
        self.conv2 = nn.Conv2d(ch, ch, 3, padding=1, bias=False)
        self.bn2   = nn.BatchNorm2d(ch)
        self.se    = SE(ch) if use_se else nn.Identity()
        self.drop  = DropPath(drop_path)

        nn.init.kaiming_normal_(self.conv1.weight, nonlinearity='relu')
        nn.init.kaiming_normal_(self.conv2.weight, nonlinearity='relu')

    def forward(self, x):
        h = F.gelu(self.bn1(self.conv1(x)))
        h = self.bn2(self.conv2(h))
        h = self.se(h)
        h = self.drop(h)
        return F.gelu(x + h)


class ChessNetConservative(nn.Module):
    """
    Minimal but solid architecture for 18-plane input.

    Input:  [B, 18, 8, 8]
    Output: policy_logits [B, 4096], value [B, 1] (normalized value if labels are)
    """
    def __init__(self, in_ch=18, width=192, n_blocks=12, drop_path_max=0.1):
        super().__init__()
        self.add_coords = AddCoords()
        stem_in = in_ch + 2  # +2 for coord channels

        # Stem
        self.stem = nn.Sequential(
            nn.Conv2d(stem_in, width, 3, padding=1, bias=False),
            nn.BatchNorm2d(width),
            nn.GELU(),
        )

        # Tower with SE blocks
        drops = torch.linspace(0, drop_path_max, steps=max(n_blocks, 1)).tolist()
        self.tower = nn.Sequential(*[
            ResBlock(width, drop_path=drops[i], use_se=True)
            for i in range(n_blocks)
        ])

        # Policy head
        self.policy_conv = nn.Conv2d(width, width, 1, bias=False)
        self.policy_bn   = nn.BatchNorm2d(width)
        self.policy_head = nn.Linear(width * 8 * 8, 4096)

        # Value head (no tanh – labels are already normalized)
        self.value_head = nn.Sequential(
            nn.Conv2d(width, width // 2, 1), nn.GELU(),
            nn.AdaptiveAvgPool2d(1),
            nn.Flatten(),
            nn.Linear(width // 2, 128), nn.GELU(),
            nn.Linear(128, 1),
        )

        nn.init.zeros_(self.policy_head.bias)

    def forward(self, x):            # x: [B,18,8,8]
        h = self.add_coords(x)       # [B,20,8,8]
        h = self.stem(h)             # [B,width,8,8]
        h = self.tower(h)            # [B,width,8,8]

        # Policy
        p = F.gelu(self.policy_bn(self.policy_conv(h)))  # [B,width,8,8]
        p = p.view(p.size(0), -1)                        # [B,width*8*8]
        p = self.policy_head(p)                          # [B,4096]

        # Value
        v = self.value_head(h)                           # [B,1]

        return p, v


# =========================================================
# Dataset 
# =========================================================

class ChessPositions(Dataset):
    """
    Dataset that loads one or more saved batches from disk.

    Expects:
      X_boards_batch_XXXX.npy  -> (N, 18, 8, 8)
      y_policy_batch_XXXX.npy  -> (N, 4096)
      y_value_batch_XXXX.npy   -> (N,)
    """
    def __init__(self, data_dir, batch_ids):
        X_list, y_pol_list, y_val_list = [], [], []

        for b in batch_ids:
            X = np.load(f"{data_dir}/X_boards_batch_{b:04d}.npy")      # (N,18,8,8)
            y_pol = np.load(f"{data_dir}/y_policy_batch_{b:04d}.npy")  # (N,4096)
            y_val = np.load(f"{data_dir}/y_value_batch_{b:04d}.npy")   # (N,)

            X_list.append(X)
            y_pol_list.append(y_pol)
            y_val_list.append(y_val)

        self.X = np.concatenate(X_list, axis=0)          # (M,18,8,8)
        self.y_pol = np.concatenate(y_pol_list, axis=0)  # (M,4096)
        self.y_val = np.concatenate(y_val_list, axis=0)  # (M,)

        self.move_idx = self.y_pol.argmax(axis=1).astype(np.int64)

    def __len__(self):
        return self.X.shape[0]

    def __getitem__(self, idx):
        x = torch.from_numpy(self.X[idx])  # (18,8,8), float32
        move_idx = torch.tensor(self.move_idx[idx], dtype=torch.long)
        value = torch.tensor(self.y_val[idx], dtype=torch.float32)
        return x, move_idx, value


def discover_batch_ids(data_dir):
    paths = sorted(glob.glob(os.path.join(data_dir, "X_boards_batch_*.npy")))
    batch_ids = []
    for p in paths:
        base = os.path.basename(p)  # e.g. X_boards_batch_0003.npy
        num_str = base.replace("X_boards_batch_", "").replace(".npy", "")
        try:
            batch_ids.append(int(num_str))
        except ValueError:
            continue
    return sorted(batch_ids)


# =========================================================
# Layer-freezing for fine-tuning
# =========================================================

def freeze_early_layers(model: ChessNetConservative, n_frozen_blocks: int = 6):
    # 1) Freeze stem
    for p in model.stem.parameters():
        p.requires_grad = False

    # 2) Freeze first n_frozen_blocks in tower, train the rest
    for i, block in enumerate(model.tower):
        if i < n_frozen_blocks:
            for p in block.parameters():
                p.requires_grad = False
        else:
            for p in block.parameters():
                p.requires_grad = True

    # 3) Always train policy + value heads
    for p in model.policy_conv.parameters():
        p.requires_grad = True
    for p in model.policy_bn.parameters():
        p.requires_grad = True
    for p in model.policy_head.parameters():
        p.requires_grad = True
    for p in model.value_head.parameters():
        p.requires_grad = True

    trainable = sum(p.numel() for p in model.parameters() if p.requires_grad)
    total = sum(p.numel() for p in model.parameters())
    print(f"Trainable params after freezing: {trainable:,} / {total:,}")


# =========================================================
# Fine-tuning loop (on tactics dataset)
# =========================================================

def main():
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print("Using device:", device)

    # ---- Use your tactics batches ----
    data_dir = "./processed_data_tactics"   # <- OUTPUT from preprocess_tactics.py
    batch_ids = discover_batch_ids(data_dir)
    print(f"Found {len(batch_ids)} tactic batches:", batch_ids)

    if not batch_ids:
        raise RuntimeError(f"No batches found in {data_dir}.")

    first_batch = np.load(f"{data_dir}/X_boards_batch_{batch_ids[0]:04d}.npy")
    est_total_positions = len(first_batch) * len(batch_ids)
    print(f"Estimated total tactics positions: ~{est_total_positions:,}")

    # ----- Build model and load pretrained weights -----
    model = ChessNetConservative(
        in_ch=18,
        width=192,
        n_blocks=12,
        drop_path_max=0.1
    ).to(device)

    # Load your big-stockfish pretrained model here
    PRETRAINED_CKPT = "chessnet_mvp_18planes_final.pt"
    state = torch.load(PRETRAINED_CKPT, map_location=device)
    model.load_state_dict(state)
    print(f"Loaded pretrained checkpoint: {PRETRAINED_CKPT}")

    # Freeze early layers, train later tower + heads
    freeze_early_layers(model, n_frozen_blocks=6)

    # Optimizer only on trainable params
    trainable_params = [p for p in model.parameters() if p.requires_grad]
    optimizer = torch.optim.AdamW(
        trainable_params,
        lr=1e-4,          # smaller LR for fine-tune
        weight_decay=1e-4,
    )

    value_loss_weight = 1.0
    num_epochs = 2       # start small; you can increase later
    value_clip = 1.0     # labels are already in [-1,1], so this is just safety

    for epoch in range(num_epochs):
        model.train()
        epoch_total_loss = 0.0
        epoch_policy_loss = 0.0
        epoch_value_loss = 0.0
        epoch_samples = 0

        print(f"\n===== Tactics Epoch {epoch+1}/{num_epochs} =====")

        for b in batch_ids:
            print(f"  → Fine-tuning on tactics batch {b:04d} ...", end="", flush=True)

            dataset = ChessPositions(data_dir, batch_ids=[b])
            loader = DataLoader(
                dataset,
                batch_size=256,
                shuffle=True,
                num_workers=2,
                pin_memory=(device.type == "cuda"),
            )

            batch_total_loss_sum = 0.0
            batch_policy_loss_sum = 0.0
            batch_value_loss_sum = 0.0
            batch_samples = 0

            for x, move_idx, value in loader:
                x = x.to(device, dtype=torch.float32, non_blocking=True)
                move_idx = move_idx.to(device, dtype=torch.long, non_blocking=True)
                value = value.to(device, dtype=torch.float32, non_blocking=True)

                # Value labels are already in [-1,1] from preprocess_tactics, but clamp anyway
                value = torch.clamp(value, -value_clip, value_clip)

                optimizer.zero_grad()

                policy_logits, value_pred = model(x)   # (B,4096), (B,1)
                value_pred = value_pred.squeeze(-1)    # (B,)
                value_pred = torch.clamp(value_pred, -value_clip, value_clip)

                policy_loss = F.cross_entropy(policy_logits, move_idx)
                value_loss = F.mse_loss(value_pred, value)

                loss = policy_loss + value_loss_weight * value_loss
                loss.backward()
                optimizer.step()

                bs = x.size(0)
                batch_samples += bs
                batch_total_loss_sum += loss.item() * bs
                batch_policy_loss_sum += policy_loss.item() * bs
                batch_value_loss_sum += value_loss.item() * bs

            epoch_samples += batch_samples
            epoch_total_loss += batch_total_loss_sum
            epoch_policy_loss += batch_policy_loss_sum
            epoch_value_loss += batch_value_loss_sum

            avg_batch_total = batch_total_loss_sum / max(batch_samples, 1)
            avg_batch_pol   = batch_policy_loss_sum / max(batch_samples, 1)
            avg_batch_val   = batch_value_loss_sum / max(batch_samples, 1)
            print(f" done. avg total={avg_batch_total:.4f}, "
                  f"policy={avg_batch_pol:.4f}, value={avg_batch_val:.4f}")

            del dataset
            del loader

        avg_epoch_total = epoch_total_loss / max(epoch_samples, 1)
        avg_epoch_pol   = epoch_policy_loss / max(epoch_samples, 1)
        avg_epoch_val   = epoch_value_loss / max(epoch_samples, 1)

        print(f"Epoch {epoch+1}: "
              f"total={avg_epoch_total:.4f}, "
              f"policy={avg_epoch_pol:.4f}, "
              f"value={avg_epoch_val:.4f}")

        ckpt_path = f"chessnet_mvp_18planes_tactics_epoch{epoch+1}.pt"
        torch.save(model.state_dict(), ckpt_path)
        print(f"Saved tactics fine-tune checkpoint: {ckpt_path}")

    final_path = "chessnet_mvp_18planes_tactics_final.pt"
    torch.save(model.state_dict(), final_path)
    print(f"Saved final fine-tuned model weights to {final_path}")


if __name__ == "__main__":
    main()
