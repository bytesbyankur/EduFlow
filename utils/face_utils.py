import face_recognition
import numpy as np
import pickle

def get_embedding(frame):
    rgb = frame[:, :, ::-1]
    encodings = face_recognition.face_encodings(rgb)
    return encodings[0] if encodings else None


def match_face(live_embedding, stored_embeddings, threshold=0.45):
    if live_embedding is None:
        return None

    ids = list(stored_embeddings.keys())
    db_encs = [pickle.loads(e) for e in stored_embeddings.values()]

    distances = face_recognition.face_distance(db_encs, live_embedding)
    best_idx = np.argmin(distances)

    if distances[best_idx] < threshold:
        return ids[best_idx]

    return None
