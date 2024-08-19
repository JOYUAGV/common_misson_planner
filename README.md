# Mission Plan
This repository is aimed to generate mission plans (including trajectory waypoints, and etc.) for unmanned veihcles from a refered mission plan.
## Usage
**Step 1: Origin alignment** 
```bash
# Function: 
# 给定当前位置（经纬高格式），将指定文件中所有非零位置进行偏移与当前位置对齐，并将结果（经纬高格式）写入指定文件
# Command:
python mission_plan_origin_alignment.py
# Parameter explanation:
# file_path = './ref1_tmp.waypoints' (specify the target waypoints that u want to align with current position)
# lon_cur = 115.84608375 (current longitude of the veihcle (deg))
# lat_cur = 39.46349718 (current latitude of the veihcle (deg))
# alt = 4.5  (specify the target altitude (m))
```

**Step 2: Trajecotry mirror and shift** 
```bash
# Function: 从指定文件中读取任务点，并对所有非零位置进行镜像与偏移，并将结果（经纬高格式）写入指定文件
# Command:
python mission_plan_mirror_shift.py
# Parameter explanation:
# file_path = './ref1_tmp_origin_alignment.waypoints'  (specify the target waypoints file that u want to mirror and shift)
# dx = 4.0  (specify the left(-)/right offset in meters)
# dy = -0.50  （specify the forward/backward(-) offset in meters）
# alt = 4.5  （specify the target altitude (m)）
```
