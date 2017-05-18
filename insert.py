import tornado.ioloop
import tornado.web, tornado.gen
import motor
import pprint
from bson.objectid import ObjectId
import numpy as np
import cv2
import os
import itertools
from skimage import io
from operator import itemgetter, attrgetter, methodcaller
import time

c = motor.MotorClient("mongodb://localhost:27017")
db = c["demo"]

class MainHandler(tornado.web.RequestHandler):

    def read(self, path):
        sift = cv2.SIFT()
        img = io.imread(path)
        img = cv2.resize(img, (128, 128))
        kp, des = sift.detectAndCompute(img, None)
        return des.tolist()

    @tornado.gen.coroutine
    def get(self):

        insert_time1 = time.time()

        f = open("test2.txt", "r")
        x = f.readlines()
        x = x[0].split(", ")
        c = 1
        for i in x:
            db.test.insert({
                "id": c,
                "image_link": "http://"+i,
                "des": self.read("http://"+i)
                })
            print "creating des for", i
            c += 1

        insert_time2 = time.time()
        print "time taken for insertion:", insert_time2 - insert_time1

        self.finish("inserted")

def make_app():
    return tornado.web.Application([
        (r"/", MainHandler),
    ])

if __name__ == "__main__":
    app = make_app()
    app.listen(8888)

    tornado.ioloop.IOLoop.current().start()
