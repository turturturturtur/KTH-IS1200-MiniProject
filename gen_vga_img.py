# gen_vga_img.py
#
# 功能：
#   生成一个符合特定 VGA 硬件要求的测试图像文件。
#
# 输出文件规格：
#   - 文件名: vga_test.bin
#   - 分辨率: 320x240 像素
#   - 颜色格式: 8-bit RGB (RRRGGGBB)，每个像素占一个字节
#   - 文件头: 无 (纯原始像素数据)
#   - 总大小: 320 * 240 = 76800 字节
#
# 图像内容：
#   一个由 16x16 像素方块组成的棋盘格，叠加了一个从左到右的水平灰度渐变。
#   这个图案有助于直观地检查显示区域、颜色和数据传输的正确性。

import numpy as np

# --- 配置参数 ---
WIDTH = 320
HEIGHT = 240
OUTPUT_FILENAME = "vga_test.bin"


def convert_gray_to_rgb332(gray_val: int) -> int:
    """
    将一个 0-255 范围的灰度值转换为一个 8-bit RRRGGGBB 格式的字节。
    
    Args:
        gray_val: 输入的灰度值 (0-255)。

    Returns:
        转换后的 8-bit RRRGGGBB 格式的字节值。
    """
    # 简单的灰度转换：让 R, G, B 三个分量都与灰度值成正比。
    # 1. 将 0-255 的灰度值按比例映射到各个分量的目标范围内。
    #    - Red   (3 bits): 范围 0-7
    #    - Green (3 bits): 范围 0-7
    #    - Blue  (2 bits): 范围 0-3
    r_3bit = int((gray_val / 255.0) * 7)
    g_3bit = int((gray_val / 255.0) * 7)
    b_2bit = int((gray_val / 255.0) * 3)

    # 2. 使用位操作将三个分量打包到一个字节中，格式为 RRRGGGBB。
    #    - 红色分量 (RRR) 移动到最高位 [7:5]
    #    - 绿色分量 (GGG) 移动到中间位 [4:2]
    #    - 蓝色分量 (BB)  保持在最低位 [1:0]
    rgb332_val = (r_3bit << 5) | (g_3bit << 2) | b_2bit
    return rgb332_val


def generate_image_data(width: int, height: int) -> np.ndarray:
    """
    生成图像的像素数据。
    
    Args:
        width: 图像宽度。
        height: 图像高度。
        
    Returns:
        一个包含图像数据的 NumPy 数组。
    """
    # 创建一个正确尺寸的空图像数组，数据类型为 8 位无符号整数。
    image_array = np.zeros((height, width), dtype=np.uint8)
    
    print("Generating pixel data...")
    # 逐个像素地填充数据
    for y in range(height):
        for x in range(width):
            # --- 生成 0-255 的灰度图案 ---
            # a) 基础图案：16x16 的棋盘格，由纯黑(0)和中灰(128)组成
            checkerboard_base = ((x // 16 + y // 16) % 2) * 128
            
            # b) 叠加图案：从左到右的水平渐变 (0 -> 255)
            horizontal_gradient = int(255 * (x / (width - 1)))
            
            # c) 组合两者，并将结果限制在 0-255 范围内
            final_gray_value = min(checkerboard_base + horizontal_gradient, 255)

            # --- 将灰度值转换为 VGA 期望的 RRRGGGBB 格式 ---
            image_array[y, x] = convert_gray_to_rgb332(final_gray_value)
            
    return image_array


def main():
    """主函数：生成图像数据并写入文件。"""
    
    # 1. 生成图像数据
    img_data = generate_image_data(WIDTH, HEIGHT)
    
    # 2. 将 NumPy 数组转换为原始字节串
    byte_data = img_data.tobytes()
    
    # 3. 将字节串写入二进制文件
    print(f"Writing data to '{OUTPUT_FILENAME}'...")
    with open(OUTPUT_FILENAME, "wb") as f:
        f.write(byte_data)
    
    # 4. 打印信息并验证文件大小
    file_size = len(byte_data)
    expected_size = WIDTH * HEIGHT
    
    print("\n--- Generation Complete ---")
    print(f"Generated file: {OUTPUT_FILENAME}")
    print(f"Resolution: {WIDTH}x{HEIGHT}")
    print(f"Expected size: {expected_size} bytes")
    print(f"Actual size:   {file_size} bytes")
    
    if file_size == expected_size:
        print("Success: File size is correct!")
    else:
        print("Error: File size is incorrect!")
    print("---------------------------\n")


if __name__ == "__main__":
    main()