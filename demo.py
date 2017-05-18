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

    @tornado.gen.coroutine
    def get(self):

        a = time.time()
        
        images_dic = yield db.test.find({'des': {'$exists': True}}).sort("id", 1).to_list(length = None)
        
        flann = cv2.FlannBasedMatcher(dict(algorithm=0, trees=5), dict(checks=50))
        
        for i in range(len(images_dic)-1):
            similar = []
            first_image_link = images_dic[i]['image_link']
            first_image_des = np.array(images_dic[i]['des'], dtype = np.float32)                   
            for j in range(i+1, len(images_dic)):
                second_image_link = images_dic[j]['image_link']
                second_image_des = np.array(images_dic[j]['des'], dtype = np.float32)
                
                matches = flann.knnMatch(first_image_des, second_image_des, 2)
                good = filter(lambda x: x[0].distance < 0.6 * x[1].distance, matches)
                l = len(good)
                if l > 2:
                    similar.append({'url': second_image_link, 'points': l})
                    
            similar = sorted(similar, reverse=True)
     
            yield db.test.update({'image_link': first_image_link}, {"$set": {"similar": similar}})
        
        b = time.time()
        print b-a
        
        print "finished"
        self.render("demo.html", title="Demo", images_list=images_dic)
      
class ViewimageHandler(tornado.web.RequestHandler):
    @tornado.gen.coroutine
    def get(self, **kargs):
        
        a = time.time()

        image_id = yield db.test.find_one({
            '_id': ObjectId(self.get_argument('id', None))
        })

        similar_images = yield db.test.find({"similar.url": image_id['image_link']}).to_list(length=None)
        
        li = []
        target = image_id['image_link']
        li.extend(image_id['similar'])
        for i in similar_images:
            if i['similar']:
                for j in i['similar']:
                    if j['url'] == target:
                        li.append({'url': i['image_link'], 'points': j['points']})
        li = sorted(li, reverse=True)
        b = time.time()
        print b-a
        
        self.render('view.html', image_id=image_id, li = li)

def make_app():
    return tornado.web.Application([
        (r"/", MainHandler),
        (r"/view", ViewimageHandler),
    ])

if __name__ == "__main__":
    app = make_app()
    app.listen(8888)

    tornado.ioloop.IOLoop.current().start()