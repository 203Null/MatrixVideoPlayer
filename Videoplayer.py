import cv2
import time
import mido
# ffpyplayer for playing audio
from ffpyplayer.player import MediaPlayer
from tkinter.filedialog import askopenfilename

# Setup
video_path = askopenfilename(title="Choose video to play")
print("Video selected: %s\n" % video_path)
video = cv2.VideoCapture(video_path)

num_of_matrixes_x = int(input("How many column Matrixes you plan to use ? (X axis)"))
num_of_matrixes_y = int(input("How many rows Matrixes you plan to use ? (Y axis)"))
previous_frame_time = 0
print()
matrixes = []
crop_x_res, crop_y_res = None, None

if num_of_matrixes_x != 0 and num_of_matrixes_y != 0:
    if video.get(cv2.CAP_PROP_FRAME_WIDTH) / video.get(cv2.CAP_PROP_FRAME_HEIGHT) > num_of_matrixes_x / num_of_matrixes_y:
        crop_x_res = video.get(cv2.CAP_PROP_FRAME_HEIGHT) * num_of_matrixes_x // num_of_matrixes_y
        crop_y_res = video.get(cv2.CAP_PROP_FRAME_HEIGHT)
    else:
        crop_x_res = video.get(cv2.CAP_PROP_FRAME_WIDTH)
        crop_y_res = video.get(cv2.CAP_PROP_FRAME_WIDTH) * num_of_matrixes_y // num_of_matrixes_x

    print("Source Aspect Ratio: %f" % (video.get(cv2.CAP_PROP_FRAME_WIDTH) / video.get(cv2.CAP_PROP_FRAME_HEIGHT)))
    print("Target Ratio: %f" % (num_of_matrixes_x / num_of_matrixes_y))
    print("Source Resolution: %d x %d" % (video.get(cv2.CAP_PROP_FRAME_WIDTH), video.get(cv2.CAP_PROP_FRAME_HEIGHT)))
    print("Crop Resolution: %f x %f" % (crop_x_res, crop_y_res))
    crop_x_res = [int((video.get(cv2.CAP_PROP_FRAME_WIDTH) - crop_x_res) // 2), int((video.get(cv2.CAP_PROP_FRAME_WIDTH) + crop_x_res) // 2)]
    crop_y_res = [int((video.get(cv2.CAP_PROP_FRAME_HEIGHT) - crop_y_res) // 2), int((video.get(cv2.CAP_PROP_FRAME_HEIGHT) + crop_y_res) // 2)]
    print("Crop Frame: %d:%d x %d:%d" % (crop_x_res[0], crop_x_res[1], crop_y_res[0], crop_y_res[1]))

target_x_res, target_y_res = num_of_matrixes_x * 8, num_of_matrixes_y * 8
print("Target Resolution: %d x %d" % (target_x_res, target_y_res))

for y in range(num_of_matrixes_y):
    matrixes.append([])
    for x in range(num_of_matrixes_x):
        print("Please pick device for (%d, %d)" % (x, y))
        midi_ports = mido.get_output_names()
        for port_id in range(len(midi_ports)):
            print("%d: %s" % (port_id + 1, midi_ports[port_id]))
        selection = int(input("Please enter the number of selected device")) - 1
        if selection == -1:
            matrixes[y].append(None)
            continue
        print("%s selected \n" % midi_ports[selection])
        matrixes[y].append(mido.open_output(midi_ports[selection]))

input("Press any key to play...")


def main():
    player = MediaPlayer(video_path)
    while True:
        audio_frame, val = player.get_frame()
        print(val)
        if val == "eof":
            break
        if val >= 0:
            grabbed, frame = video.read()
            if not grabbed:
                print("End of video")
                break
            if cv2.waitKey(1) & 0xFF == ord("q"):
                break
            cv2.imshow("Video", frame)
            renderToMatrixes(frame)
            time.sleep(val)
    video.release()
    cv2.destroyAllWindows()


def renderToMatrixes(img):
    cropped_img = img[crop_y_res[0]:crop_y_res[1], crop_x_res[0]:crop_x_res[1]]
    target_img = cv2.resize(cropped_img, (target_x_res, target_y_res)) #, interpolation = cv2.INTER_LINEAR)
    for x in range(num_of_matrixes_x):
        for y in range(num_of_matrixes_y):
            renderToMatrix(target_img[y * 8: y * 8 + 8, x * 8: x * 8 + 8], matrixes[y][x])

def renderToMatrix(img, matrix):
    if matrix == None:
        return
    msg = [0, 2, 3, 1, 0, 18, 35, 0B00010000, 4, 0]
    for x in range(8):
        for y in range(8):
            pixel = img[x, y]
            msg.append(convert8bitTo7bit(pixel[2]))
            msg.append(convert8bitTo7bit(pixel[1]))
            msg.append(convert8bitTo7bit(pixel[0]))
    # msg.append(240)
    msg = mido.Message('sysex', data=msg)
    matrix.send(msg)
    return

def convert8bitTo7bit(input):
    return input >> 1

main()
