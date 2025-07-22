import cv2, pickle, numpy as np, os, csv, time
from sklearn.neighbors import KNeighborsClassifier
import requests

class FacialRecognizer:
    def __init__(self):
        if not os.path.exists('data/faces_data.pkl'):
            self.faces = []
            self.labels = []
        self.facedetect = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
        with open('data/voter_id.pkl', 'rb') as f:
            self.labels = list(pickle.load(f))
        with open('data/faces_data.pkl', 'rb') as f:
            self.faces = list(pickle.load(f))
        self.knn = KNeighborsClassifier(n_neighbors=5)
        self.knn.fit(self.faces, self.labels)
    def register_user(self, voter_id):
        count = 0
        MAX = 50
        video = cv2.VideoCapture(0)
        while count < MAX:
            ret, frame = video.read()
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            faces = self.facedetect.detectMultiScale(gray, 1.3, 5)
            for (x, y, w, h) in faces:
                crop = frame[y:y+h, x:x+w]
                resized = cv2.resize(crop, (50, 50)).flatten()
                self.faces.append(resized.flatten())
                self.labels.append(voter_id)
                count += 1
            cv2.imshow("Registering...", frame)
            if cv2.waitKey(1) == 27:
                break
        video.release()
        cv2.destroyAllWindows()
        with open('data/faces_data.pkl', 'wb') as f:
            pickle.dump(self.faces, f)
        with open('data/voter_id.pkl', 'wb') as f:
            pickle.dump(self.labels, f)

    
    def recognize(self):
        video = cv2.VideoCapture(0)
        output = None
        start_time = time.time()
        timeout = 5  # seconds to wait for a face

        print("🔍 Please look at the camera to verify your identity...")

        while True:
            ret, frame = video.read()
            if not ret:
                break

            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            faces = self.facedetect.detectMultiScale(gray, 1.3, 5)

            if len(faces) > 0:
                for (x, y, w, h) in faces:
                    crop_img = frame[y:y+h, x:x+w]
                    resized_img = cv2.resize(crop_img, (50, 50)).flatten().reshape(1, -1)
                    output = self.knn.predict(resized_img)[0]

                    # Optional: Show detection box
                    cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)
                    cv2.putText(frame, f"Recognized: {output}", (x, y - 10),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)

                    video.release()
                    cv2.destroyAllWindows()
                    print(f"✅ Face recognized: {output}")
                    return output  # Success

            else:
                # Optional: Show countdown
                remaining = timeout - int(time.time() - start_time)
                cv2.putText(frame, f"Searching... {remaining}s", (20, 30),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)

            cv2.imshow("Verifying Face...", frame)
            if cv2.waitKey(1) == 27 or time.time() - start_time > timeout:
                break

        video.release()
        cv2.destroyAllWindows()
        print("❌ No face detected within time limit.")
        return None


    def has_already_voted(self, voter_id):
        try:
            with open("Votes.csv", "r") as f:
                return any(row[0] == voter_id for row in csv.reader(f))
        except FileNotFoundError:
            return False

    def record_vote(self, voter_id, candidate):
    # Send vote to blockchain backend
        try:
            response = requests.post(
                "http://127.0.0.1:5001/vote",
                json={"candidate": candidate}
            )
            result = response.json()
            print(f"[Blockchain] Vote response: {result}")
            return result
        except requests.exceptions.RequestException as e:
            print(f"[ERROR] Failed to send vote to blockchain: {e}")
            return {"status": "error", "message": "Blockchain vote failed"}
