from flask import Flask, render_template, Response
import cv2

app = Flask(__name__)

# Use command v4l2-ctl --list-devices
camera = cv2.VideoCapture('/dev/video0', cv2.CAP_V4L)  # Use 0 for web camera

# Set the resolution
camera.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

def gen_frames():  
    print('Estamos en gen_frames')
    while True:
        success, frame = camera.read()  # read the camera frame
        print('Resultado de success: ' + str(success))
        if not success:
            break
        else:
            ret, buffer = cv2.imencode('.jpg', frame)
            frame = buffer.tobytes()
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')  # concat frame one by one and show result

@app.route('/video_feed')
def video_feed():
    return Response(gen_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port='5000')