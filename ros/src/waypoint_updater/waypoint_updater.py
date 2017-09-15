#!/usr/bin/env python

import rospy
from geometry_msgs.msg import PoseStamped
from styx_msgs.msg import Lane, Waypoint

import math
import tf
import numpy as np

import matplotlib.pyplot as plt
import matplotlib.patches as patches

'''
This node will publish waypoints from the car's current position to some `x` distance ahead.

As mentioned in the doc, you should ideally first implement a version which does not care
about traffic lights or obstacles.

Once you have created dbw_node, you will update this node to use the status of traffic lights too.

Please note that our simulator also provides the exact location of traffic lights and their
current status in `/vehicle/traffic_lights` message. You can use this message to build this node
as well as to verify your TL classifier.

TODO (for Yousuf and Aaron): Stopline location for each traffic light.
'''

LOOKAHEAD_WPS = 10 # Number of waypoints we will publish. You can change this number


class WaypointUpdater(object):
    def __init__(self):
        rospy.init_node('waypoint_updater')

        rospy.Subscriber('/current_pose', PoseStamped, self.pose_cb)
        rospy.Subscriber('/base_waypoints', Lane, self.waypoints_cb)

        # TODO: Add a subscriber for /traffic_waypoint and /obstacle_waypoint below


        self.final_waypoints_pub = rospy.Publisher('final_waypoints', Lane, queue_size=1)

        # TODO: Add other member variables you need below
        self.TrG2V = 0 #transformation globe 2 vehicle
        self.TrV2G = 0
        self.FirstTime = True
        self.waypointsInVehicleCoordinate = None
        self.WPs = []   # as list of transfer matrices of first position
                                                        # second globe to wp
        self.posi = None
        plt.ion()
        rospy.spin()

    def pose_cb(self, msg):
        # TODO: Implement
        p = msg.pose.position
        self.posi = p
        o = msg.pose.orientation
        t1 = tf.transformations.translation_matrix([p.x, p.y, p.z])
        t2 = tf.transformations.quaternion_matrix([o.x,o.y,o.z,o.w])
        self.TrV2G = tf.transformations.concatenate_matrices(t1,t2)
        self.TrG2V = tf.transformations.inverse_matrix(self.TrV2G)

    def waypoints_cb(self, waypoints):
        # TODO: Implement
        #waypointsInVehicleFrame = Lane()
        #for waypoint in waypoints.waypoints:
        #    pass
        if self.FirstTime is True:
            self.FirstTime = False
            self.init_WPs(waypoints.waypoints)
            #self.plot_waypoints(waypoints)
        self.find_final_WP()

    def init_WPs(self,waypoints):
        for waypoint in waypoints:
            p = waypoint.pose.pose.position
            o = waypoint.pose.pose.orientation
            t1 = tf.transformations.translation_matrix((p.x, p.y, p.z))
            t2 = tf.transformations.quaternion_matrix([o.x, o.y, o.z, o.w])
            Twp2g = tf.transformations.concatenate_matrices(t2, t1)
            Tg2wp = tf.transformations.inverse_matrix(Twp2g)
            pos = np.array([p.x, p.y, p.z,1.0])
            pos.reshape((4,1))
            self.WPs.append( [pos , Tg2wp] )

    def find_final_WP(self):
        idx = self.find_closest_WP_2_car()
        if idx is not None:
            rospy.logwarn(idx)
            #pass
        else:  # handle this error. Maybe backward motion??
            rospy.logwarn("There is no waypoint in front of the car.")
            #pass
        self.plot()

    def plot(self):
        plt.clf()
        plt.plot([x[0][0] for x in self.WPs],
                 [x[0][1] for x in self.WPs])
        plt.plot(self.TrV2G[0,3],self.TrV2G[1,3],marker = 'o',color='green')
        plt.plot(self.posi.x, self.posi.y, marker='o',color='red')
        plt.axis('equal')
        plt.pause(0.001)

    def find_closest_WP_2_car(self):
        min_dist = float('inf')
        idx = None
        for i , WP in enumerate(self.WPs):
            posWP = WP[0]
            wpInVH = self.TrG2V.dot(posWP)
            dst = np.linalg.norm(wpInVH[:3])
            if (wpInVH[0] > 0.0 and dst < min_dist):
                min_dist = dst
                idx = i
        return idx

    def traffic_cb(self, msg):
        # TODO: Callback for /traffic_waypoint message. Implement
        pass

    def obstacle_cb(self, msg):
        # TODO: Callback for /obstacle_waypoint message. We will implement it later
        pass

    def get_waypoint_velocity(self, waypoint):
        return waypoint.twist.twist.linear.x

    def set_waypoint_velocity(self, waypoints, waypoint, velocity):
        waypoints[waypoint].twist.twist.linear.x = velocity

    def distance(self, waypoints, wp1, wp2):
        dist = 0
        dl = lambda a, b: math.sqrt((a.x-b.x)**2 + (a.y-b.y)**2  + (a.z-b.z)**2)
        for i in range(wp1, wp2+1):
            dist += dl(waypoints[wp1].pose.pose.position, waypoints[i].pose.pose.position)
            wp1 = i
        return dist

    def Transfer2VehicleCoordinate(self,waypoints):
        self.waypointsInVehicleCoordinate = []
        for waypoint in waypoints.waypoints:
            x = waypoint.pose.pose.position.x
            y = waypoint.pose.pose.position.y
            z = waypoint.pose.pose.position.z

            pos = np.array([x,y,z],np.float32)
            self.waypointsInVehicleCoordinate.append(self.TrG2V * pos)

    def plot_waypoints(self,waypoints):
        x, y, z, T = [], [], [], []
        for waypoint in waypoints.waypoints:
            x.append(waypoint.pose.pose.position.x)
            y.append(waypoint.pose.pose.position.y)
            z.append(waypoint.pose.pose.position.z)
            ox = waypoint.pose.pose.orientation.x
            oy = waypoint.pose.pose.orientation.y
            oz = waypoint.pose.pose.orientation.z
            ow = waypoint.pose.pose.orientation.w
            # rospy.loginfo([ox,oy,oz,ow])
            T.append( tf.transformations.quaternion_matrix([ox, oy, oz, ow]) )
            # eulers = tf.transformations.euler_from_quaternion([ox,oy,oz,ow])
            # orients.append( [50.0*math.cos(eulers[2]),50.0*math.sin(eulers[2])])
            # rospy.loginfo(tf.transformations.euler_from_quaternion([ox,oy,oz,ow]))
        plt.plot(x, y)
        ax = plt.gca()
        for i in range(0, len(x), 100):
            ax.add_patch(patches.Arrow(x[i], y[i], 50 * T[i][0, 0], 50 * T[i][1, 0], width=10))
            ax.add_patch(patches.Arrow(x[i], y[i], 50 * T[i][0, 1], 50 * T[i][1, 1], width=10))
            # rospy.loginfo([x[i],y[i],orients[i][0],orients[i][1]])
        plt.axis('equal')
        plt.show()


if __name__ == '__main__':
    try:
        WaypointUpdater()
    except rospy.ROSInterruptException:
        rospy.logerr('Could not start waypoint updater node.')
