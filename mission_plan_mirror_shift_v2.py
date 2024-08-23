#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Author: Weihong Liu
Email: liuweihong_cau@163.com
"""

import os
import numpy as np
import pyproj

def parse_wpl_file(file_path):
    with open(file_path, 'r') as file:
        lines = file.readlines()

    waypoints = []
    for line in lines[1:]:  # Skip the first line (header)
        parts = line.strip().split('\t')
        try:
            index = int(parts[0])
            frame = int(parts[1])
            command = int(parts[2])
            param0 = int(float(parts[3]))
            param1 = int(float(parts[4]))
            param2 = int(float(parts[5]))
            param3 = int(float(parts[6]))
            param4 = int(float(parts[7]))
            lat = float(parts[8]) if parts[8] else None
            lon = float(parts[9]) if parts[9] else None
            alt = float(parts[10]) if parts[10] else None
            autocontinue = int(float(parts[11])) if parts[11] else None

            wp = {
                'index': index,
                'frame': frame,
                'command': command,
                'param0': param0, 
                'param1': param1,
                'param2': param2,
                'param3': param3,
                'param4': param4,
                'lat': lat,
                'lon': lon,
                'alt': alt,
                'autocontinue': autocontinue
            }
            waypoints.append(wp)
        except ValueError as e:
            print(f"Error parsing line: {line}\n{e}")
            continue

    return waypoints

def get_utm_zone(lon):
    return int((lon + 180) / 6) + 1

def generate_mirror_line(lat1, lon1, lat2, lon2):
    wgs84 = pyproj.Proj(proj='latlong', datum='WGS84')
    utm_zone = get_utm_zone(lon1)
    utm = pyproj.Proj(proj='utm', zone=utm_zone, datum='WGS84')
    transformer_to_utm = pyproj.Transformer.from_proj(wgs84, utm)
    
    x1, y1 = transformer_to_utm.transform(lon1, lat1)
    x2, y2 = transformer_to_utm.transform(lon2, lat2)
    
    A = y2 - y1
    B = x1 - x2
    C = x2 * y1 - x1 * y2
    
    length = np.sqrt(A**2 + B**2)
    A /= length
    B /= length
    C /= length
    
    return A, B, C

def mirror_point(x0, y0, A, B, C):
    d = (A * x0 + B * y0 + C) / np.sqrt(A**2 + B**2)
    x_p = x0 - (A * (A * x0 + B * y0 + C)) / (A**2 + B**2)
    y_p = y0 - (B * (A * x0 + B * y0 + C)) / (A**2 + B**2)
    x_mirror = 2 * x_p - x0
    y_mirror = 2 * y_p - y0
    return x_mirror, y_mirror

def generate_mirrored_and_offset_waypoints(waypoints, dx, dy, alt1, alt2):
    if not waypoints:
        raise ValueError("No waypoints available to process.")
    
    wgs84 = pyproj.Proj(proj='latlong', datum='WGS84')
    
    wp3 = next((wp for wp in waypoints if wp['index'] == 3), None)
    wp4 = next((wp for wp in waypoints if wp['index'] == 4), None)
    
    if wp3 is None or wp4 is None:
        raise ValueError("Cannot find waypoints with index 3 and 4.")
    
    lon1, lat1 = wp3['lon'], wp3['lat']
    lon2, lat2 = wp4['lon'], wp4['lat']
    
    A, B, C = generate_mirror_line(lat1, lon1, lat2, lon2)
    
    utm_zone = get_utm_zone(lon1)
    utm = pyproj.Proj(proj='utm', zone=utm_zone, datum='WGS84')
    transformer_to_utm = pyproj.Transformer.from_proj(wgs84, utm)
    transformer_to_latlon = pyproj.Transformer.from_proj(utm, wgs84)
    
    mirrored_and_offset_waypoints = []

    for wp in waypoints:
        lat, lon = wp['lat'], wp['lon']
        if lat is not None and lon is not None and lat != 0 and lon != 0:
            x, y = transformer_to_utm.transform(lon, lat)
            
            if wp['index'] in [4]:
                # Apply offsets
                x_offset = x + dx
                y_offset = y + dy
                lon5_new, lat5_new = transformer_to_latlon.transform(x_offset, y_offset)
            if wp['index'] in [3]:
                # Apply offsets
                x_offset = x + dx
                y_offset = y + dy
                lon6_new, lat6_new = transformer_to_latlon.transform(x_offset, y_offset)
             
            new_wp = wp.copy()
            new_wp['lat'] = lat
            new_wp['lon'] = lon
            if wp['index'] in [5]:
                new_wp['lon'] = lon5_new
                new_wp['lat'] = lat5_new   # Set altitude to new value
            if wp['index'] in [6]:
                new_wp['lon'] = lon6_new 
                new_wp['lat'] = lat6_new   # Set altitude to new value

            if wp['index'] in [0, 1, 2, 3, 4]:
                new_wp['alt'] = alt1  # Set altitude to new value
            if wp['index'] in [5, 6, 7]:
                new_wp['alt'] = alt2  # Set altitude to new value

            mirrored_and_offset_waypoints.append(new_wp)
        else:
            # Set altitude to new value for points with zero latitude or longitude
            new_wp = wp.copy()
            if wp['index'] in [0, 1, 2, 3, 4]:
                new_wp['alt'] = alt1  # Set altitude to new value
            if wp['index'] in [5, 6, 7]:
                new_wp['alt'] = alt2  # Set altitude to new value

            mirrored_and_offset_waypoints.append(new_wp)
    
    return mirrored_and_offset_waypoints

def create_wpl_content(waypoints):
    content = ["QGC WPL 110"]
    for wp in waypoints:
        line = (f"{wp['index']}\t"
                f"{wp['frame']}\t"
                f"{wp['command']}\t"
                f"{wp['param0']}\t" 
                f"{wp['param1']}\t"
                f"{wp['param2']}\t"
                f"{wp['param3']}\t"
                f"{wp['param4']}\t"
                f"{wp['lat']:.8f}\t"
                f"{wp['lon']:.8f}\t"
                f"{wp['alt']:.6f}\t"
                f"{wp['autocontinue']}")
        content.append(line)
    return "\n".join(content)

def main(file_path, dx, dy, alt1, alt2, task_index):
    waypoints = parse_wpl_file(file_path)
    if not waypoints:
        print("No valid waypoints found. Exiting.")
        return
    
    mirrored_and_offset_waypoints = generate_mirrored_and_offset_waypoints(waypoints, dx, dy, alt1, alt2)
    new_wpl_content = create_wpl_content(mirrored_and_offset_waypoints)
    
    new_file_path = os.path.splitext(file_path)[0] + '_mirrored_offset_' + str(task_index) + '_v2.waypoints'
    # new_file_path = os.path.splitext(file_path)[0] + 'ref_tmp.waypoints'
    with open(new_file_path, 'w') as file:
        file.write(new_wpl_content)
    
    print(f"偏移航线已保存到: {new_file_path}")

# Example usage
'''
Function: 从指定文件中读取任务点，并对指定index航点进行偏移，并将结果（经纬高格式）写入指定文件
'''
file_path = './ref1_tmp_origin_alignment_v2.waypoints'  # specify the target waypoints file that u want to mirror and shift
# dx = 4.0  # specify the left(-)/right offset in meters
# dy = -0.50  # specify the forward/backward(-) offset in meters
# alt = 4.5  # specify the target altitude (m)
task_table = np.array([[4.0, -0.5, 4.5],
                       [5.0, 0.0, 5.5],
                       [6.0, 0.5, 6.5],
                       [7.0, 1.0, 7.5],
                       [6.0, 0.0, 6.0],
                       [7.0, -0.5, 6.0],
                       [4.0, 1.0, 6.0],
                       [5.0, 0.5, 6.0], #8
                       [7.0, 0.5, 5.0], #9
                       [6.0, 1.0, 5.0], #10
                       [5.0, -0.5, 7.0], #11
                       [4.0, 0.0, 7.0], #12
                       [5.0, 1.0, 5.5], #13
                       [4.0, 0.5, 6.5], #14
                       [7.0, 0.0, 5.5], #15
                       [6.0, -0.5, 6.5]]) #16
task_sheldue = np.zeros((16, 3))
task_sheldue[:] = task_table
task_index = 15 # 1~16
alt1 = 6.0
dx, dy, alt2 = task_sheldue[task_index-1]
flag_cali = 0
dx += flag_cali * 0.029508704552426934      
dy += flag_cali * 0.35594024136662483
main(file_path, dx, dy, alt1, alt2, task_index)
