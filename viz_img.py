#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
可视化 raw 二进制图像（8-bit 灰度），把输入/输出并排显示。
支持自动猜尺寸（平方根），或手动指定宽高。
"""

import argparse, math, numpy as np
import matplotlib.pyplot as plt
from pathlib import Path

def load_bytes(path: Path) -> np.ndarray:
    data = np.fromfile(path, dtype=np.uint8)
    if data.size == 0:
        raise ValueError(f"{path} 为空或不可读")
    return data

def guess_hw(n: int):
    s = int(math.isqrt(n))
    if s * s == n:
        return s, s
    default_w = 256 if n >= 256 else 32
    h = n // default_w
    if h == 0:
        default_w = max(1, n)
        h = 1
    return h, default_w

def reshape(img_1d: np.ndarray, H: int, W: int) -> np.ndarray:
    need = H * W
    if img_1d.size < need:
        pad = np.zeros(need - img_1d.size, dtype=np.uint8)
        img_1d = np.concatenate([img_1d, pad])
    elif img_1d.size > need:
        img_1d = img_1d[:need]
    return img_1d.reshape(H, W)

def main():
    ap = argparse.ArgumentParser(description="可视化输入/输出 raw 灰度图像（8-bit）并排显示")
    ap.add_argument("--inp", default="img.bin", help="输入图像（二进制），默认=img.bin")
    ap.add_argument("--out", default="out.bin", help="输出图像（二进制），默认=out.bin")
    ap.add_argument("--width", type=int, default=32, help="图像宽度，默认=32")
    ap.add_argument("--height", type=int, default=32, help="图像高度，默认=32")
    ap.add_argument("--save", default=None, help="保存图像文件，例如 result.png（默认不保存，只显示）")
    args = ap.parse_args()

    inp = load_bytes(Path(args.inp))
    out = load_bytes(Path(args.out))

    if args.width and args.height:
        H, W = args.height, args.width
    else:
        n = min(inp.size, out.size)
        H, W = guess_hw(n)

    img_in  = reshape(inp,  H, W)
    img_out = reshape(out, H, W)

    inv_est = (np.mean((img_in.astype(np.uint16) + img_out.astype(np.uint16)) % 256) >= 254)

    fig, axes = plt.subplots(1, 2, figsize=(8, 4))
    axes[0].imshow(img_in, cmap="gray", vmin=0, vmax=255)
    axes[0].set_title(f"INPUT  ({img_in.shape[1]}x{img_in.shape[0]})")
    axes[0].axis("off")

    axes[1].imshow(img_out, cmap="gray", vmin=0, vmax=255)
    axes[1].set_title(f"OUTPUT ({img_out.shape[1]}x{img_out.shape[0]})" + ("  [≈ inverted]" if inv_est else ""))
    axes[1].axis("off")

    plt.tight_layout()

    if args.save:
        plt.savefig(args.save, dpi=150)
        print(f"Saved -> {args.save}")
    else:
        plt.show()

if __name__ == "__main__":
    main()
