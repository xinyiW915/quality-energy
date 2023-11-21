import numpy as np
import os

def get_video_frame_count(yuv_filename, width, height):
    frame_size = width * height * 3 // 2
    file_size = os.path.getsize(yuv_filename)
    frame_count = file_size // frame_size
    return frame_count

def calculate_mse(frame1, frame2):
    return np.mean((frame1 - frame2) ** 2)

def calculate_psnr(mse, max_value=255):
    if mse == 0:
        return float('inf')
    return 10 * np.log10((max_value ** 2) / mse)

def calculate_psnr_for_YUV(original_yuv_file, compressed_yuv_file, width, height):
    original_yuv = np.fromfile(original_yuv_file, dtype=np.uint8)
    compressed_yuv = np.fromfile(compressed_yuv_file, dtype=np.uint8)
    original_frame_count = get_video_frame_count(original_yuv_file, width, height)
    compressed_frame_count = get_video_frame_count(compressed_yuv_file, width, height)

    print('Open original video and compressed video yuv files')
    print(f'original_frame_count: {original_frame_count}')
    print(type(original_yuv))
    print(original_yuv.size)
    print(original_yuv.shape)
    print(f'compressed_frame_count: {compressed_frame_count}')
    print(compressed_yuv.shape)
    print('---------------')

    frame_size = width * height * 3 // 2
    original_yuv = original_yuv.reshape((original_frame_count, frame_size))

    # Remove the first frame from the compressed video
    compressed_yuv = compressed_yuv[frame_size:]
    compressed_frame_count -= 1
    compressed_yuv = compressed_yuv.reshape((compressed_frame_count, frame_size))

    print('Remove the first frame from the compressed video')
    print(f'original_frame_count: {original_frame_count}')
    print(original_yuv.shape)
    print(f'compressed_frame_count: {compressed_frame_count}')
    print(compressed_yuv.shape)
    print('---------------')

    # Split Y, U, and V channels
    original_y = original_yuv[:, :width * height]
    original_uv = original_yuv[:, width * height:]
    original_u = original_uv[:, ::2]  # Extract every second element for U channel
    original_v = original_uv[:, 1::2]  # Extract every second element for V channel
    print(original_y.shape)
    print(original_uv.shape)
    print(original_u.shape)
    print(original_v.shape)
    print('---------------')

    compressed_y = compressed_yuv[:, :width * height]
    compressed_uv = compressed_yuv[:, width * height:]
    compressed_u = compressed_uv[:, ::2]  # Extract every second element for U channel
    compressed_v = compressed_uv[:, 1::2]  # Extract every second element for V channel
    print(compressed_y.shape)
    print(compressed_u.shape)
    print(compressed_v.shape)
    print('---------------')

    mse_list = []

    for i in range(original_frame_count):
        mse_y = calculate_mse(original_y[i], compressed_y[i])
        mse_u = calculate_mse(original_u[i], compressed_u[i])
        mse_v = calculate_mse(original_v[i], compressed_v[i])
        mse_list.append((mse_y, mse_u, mse_v))
        print(f'frame {i}: mse_y = {mse_y}, mse_u={mse_u}, mse_v={mse_v}')
    mse_value = np.mean(mse_list, axis=0)

    max_value = 255  # Assuming the pixel values are in the range [0, 255]
    psnr_y = calculate_psnr(mse_value[0], max_value)
    psnr_u = calculate_psnr(mse_value[1], max_value)
    psnr_v = calculate_psnr(mse_value[2], max_value)

    average_psnr = (6 * psnr_y + psnr_u + psnr_v) / 8

    return psnr_y, psnr_u, psnr_v, average_psnr

qp = 50
original_yuv_file = "Gaming.yuv"
compressed_yuv_file = f"Gaming_decoded_qp{qp}.yuv"
width = 3840
height = 2160

psnr_y, psnr_u, psnr_v, average_psnr = calculate_psnr_for_YUV(original_yuv_file, compressed_yuv_file, width, height)

print(f"PSNR_Y: {psnr_y} dB")
print(f"PSNR_U: {psnr_u} dB")
print(f"PSNR_V: {psnr_v} dB")
print(f"Average PSNR: {average_psnr} dB")


