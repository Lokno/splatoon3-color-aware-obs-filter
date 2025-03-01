import obspython as obs
import cv2
import numpy as np
import sys
import time
from pygrabber.dshow_graph import FilterGraph

from requests import post

source_name = ""
filter_name = ""
update_interval = 34
running = False
default_color = 0
last_301_frame = 0

# Home Assistant globals
ha_enabled = False
ha_url = ""
ha_bearer_token = ""
ha_light_names = []

class ImgTemplate:
    def __init__(self,file_name,name,threshold,pos,cooldown=1,on_match=None):
        self.img = cv2.imread(file_name,0)
        self.dims = self.img.shape[::-1]
        self.last_matched = None
        self.name = name
        self.threshold = threshold
        self.on_match = on_match
        self.cooldown = cooldown
        self.pos = pos
    def match(self,frame_idx,frame_bgr,frame_gray):
        if self.last_matched and (frame_idx-self.last_matched) < self.cooldown:
            return False

        res = cv2.matchTemplate(frame_gray,self.img,cv2.TM_SQDIFF_NORMED)
        min_val, _, min_loc, _ = cv2.minMaxLoc(res)

        correct_position = abs(min_loc[0]-self.pos[0]) < 2 and abs(min_loc[1]-self.pos[1]) < 2
        if min_val < self.threshold and correct_position:
            if self.on_match:
                self.on_match(self,frame_idx,frame_bgr,frame_gray,min_val,min_loc)
            self.last_matched = frame_idx
        return min_val < self.threshold


def sample_color(frame_bgr, x, y, kn):
    return np.average(frame_bgr[y:y+kn,x:x+kn], axis = (0,1))

def calc_luminance( r, g, b ):
    return 0.2126 * r + 0.7152 * g + 0.0722 * b

def on_301_timer(t,frame_idx,frame_rgb,frame_gray,val,loc):
    print("Detected 3:01")
    global last_301_frame
    last_301_frame = frame_idx

def on_300_timer(t,frame_idx,frame_rgb,frame_gray,val,loc):
    print("Detected 3:00")
    global last_301_frame
    if (frame_idx-last_301_frame) > 60:
        on_battle(t,frame_idx,frame_rgb,frame_gray,val,loc)

def on_battle(t,frame_idx,frame_rgb,frame_gray,val,loc):
    print(f'Timer detected! ({val:f})')
    b,g,r = sample_color(frame_rgb,566,34,4)
    print(f'Ink Color: {r},{g},{b}')

    if calc_luminance(r, g, b) > 50.0:
        update_filter_parameter(r/255.0, g/255.0, b/255.0, True)

def on_sr_wave(t,frame_idx,frame_rgb,frame_gray,val,loc):
    print(f'Wave Detected! ({val:f})')
    #b,g,r = sample_color(frame_rgb,86,179,4)
    b,g,r = sample_color(frame_rgb,104,237,4)
    print(f'Ink Color: {r},{g},{b}')

    if calc_luminance(r, g, b) > 50.0:
        update_filter_parameter(r/255.0, g/255.0, b/255.0, True)

def update_home_devices(r,g,b):
    global ha_light_names
    global ha_enabled
    global ha_bearer_token
    global ha_url

    if ha_enabled:
        url = f"{ha_url}/api/services/light/turn_on"
        headers = { "Authorization": ha_bearer_token, 'Content-Type': 'application/json'}
        for light in ha_light_names:
            data = {"entity_id": light, "rgbw_color": [r*255,g*255,b*255,0]}
            response = post(url, headers=headers, json=data)

def update_filter_parameter(r, g, b, use_to):

    update_home_devices(r,g,b)

    source = obs.obs_get_source_by_name(source_name)
    if source:
        filter_ = obs.obs_source_get_filter_by_name(source, filter_name)
        if filter_:
            settings = obs.obs_source_get_settings(filter_)
            if settings:

                if use_to:
                    fr = obs.obs_data_get_double(settings, "to_red")
                    fg = obs.obs_data_get_double(settings, "to_green")
                    fb = obs.obs_data_get_double(settings, "to_blue")
    
                    obs.obs_data_set_double(settings, "from_red",   fr)
                    obs.obs_data_set_double(settings, "from_green", fg)
                    obs.obs_data_set_double(settings, "from_blue",  fb)
                else:
                    obs.obs_data_set_double(settings, "to_red",   r)
                    obs.obs_data_set_double(settings, "to_green", g)
                    obs.obs_data_set_double(settings, "to_blue",  b)

                    obs.obs_data_set_double(settings, "from_red",   r)
                    obs.obs_data_set_double(settings, "from_green", g)
                    obs.obs_data_set_double(settings, "from_blue",  b)         

                obs.obs_data_set_double(settings, "to_red",   r)
                obs.obs_data_set_double(settings, "to_green", g)
                obs.obs_data_set_double(settings, "to_blue",  b)

                start_time = obs.os_gettime_ns() / 1000000000.0
                obs.obs_data_set_double(settings, "start_time",  start_time)
                obs.obs_data_set_double(settings, "timestamp", time.time())

                obs.obs_source_update(filter_, settings)
                obs.obs_data_release(settings)
            obs.obs_source_release(filter_)
        obs.obs_source_release(source)

def script_properties():
    devices = FilterGraph().get_input_devices()

    props = obs.obs_properties_create()
    obs.obs_properties_add_bool(props, "running", "Running")

    # Home Assistant Settings
    obs.obs_properties_add_bool(props, "ha_enabled", "Enable Home Assistant")
    obs.obs_properties_add_text(props, "ha_url", "Home Assistant URL", obs.OBS_TEXT_DEFAULT)
    obs.obs_properties_add_text(props, "ha_bearer_token", "Home Assistant Bearer Token", obs.OBS_TEXT_DEFAULT)
    obs.obs_properties_add_text(props, "ha_light_names", "Home Assistant Lights", obs.OBS_TEXT_MULTILINE)

    obs.obs_properties_add_text(props, "source_name", "Source Name", obs.OBS_TEXT_DEFAULT)
    obs.obs_properties_add_text(props, "filter_name", "Filter Name", obs.OBS_TEXT_DEFAULT)

    camListProp = obs.obs_properties_add_list(props, "device_list", "Video Capture Device", obs.OBS_COMBO_TYPE_LIST, obs.OBS_COMBO_FORMAT_STRING)
    obs.obs_property_list_add_string(camListProp, "Select Device", "")
    for idx,name in enumerate(devices):
        obs.obs_property_list_add_string(camListProp, name, str(idx))

    obs.obs_properties_add_path(props, "sr_timer_template", "SR Timer Template", obs.OBS_PATH_FILE, "*.png;;*.jpg", "" )
    obs.obs_properties_add_float(props,"sr_timer_cooldown", "SR Timer Detect Cooldown", 0, 60, 0.1)
    obs.obs_properties_add_float_slider(props,"sr_timer_confidence", "SR Timer Confidence Value", 0, 1, 0.01)

    obs.obs_properties_add_path(props, "turf_timer_template", "Turf Timer Template", obs.OBS_PATH_FILE, "*.png;;*.jpg", "" )
    obs.obs_properties_add_float(props,"turf_timer_cooldown", "Turf Timer Detect Cooldown", 0, 60, 0.1)
    obs.obs_properties_add_float_slider(props,"turf_timer_confidence", "Turf Timer Confidence Value", 0, 1, 0.01)

    obs.obs_properties_add_path(props, "timer_301_template", "3:01 Timer Template", obs.OBS_PATH_FILE, "*.png;;*.jpg", "" )
    obs.obs_properties_add_float(props,"timer_301_cooldown", "3:01 Timer Detect Cooldown", 0, 60, 0.1)
    obs.obs_properties_add_float_slider(props,"timer_301_confidence", "3:01 Timer Confidence Value", 0, 1, 0.01)

    obs.obs_properties_add_path(props, "rank_timer_template", "Ranked Timer Template", obs.OBS_PATH_FILE, "*.png;;*.jpg", "" )
    obs.obs_properties_add_float(props,"rank_timer_cooldown", "Ranked Timer Detect Cooldown", 0, 60, 0.1)
    obs.obs_properties_add_float_slider(props,"rank_timer_confidence", "Ranked Timer Confidence Value", 0, 1, 0.01)
    
    obs.obs_properties_add_color(props,"default_color", "Default Color")

    return props

def int_to_rgb(color_int):
    return color_int & 0xFF, ((color_int & 0xffffff) >> 8) & 0xFF, ((color_int & 0xffffff) >> 16) & 0xFF

last_device_id = None
frame_count = 0
templates = {}
vid = None

def script_load(settings):
    pass

def script_update(settings):
    global source_name
    global filter_name
    global frame_count
    global vid
    global templates
    global last_device_id
    global running
    global default_color

    global ha_light_names
    global ha_enabled
    global ha_bearer_token
    global ha_url

    frame_count = 0

    running = obs.obs_data_get_bool(settings, "running")

    if not running:
        return

    # Get Home Assistant Settings
    ha_enabled = obs.obs_data_get_bool(settings, "ha_enabled")
    ha_url = obs.obs_data_get_string(settings, "ha_url")
    ha_bearer_token = obs.obs_data_get_string(settings, "ha_bearer_token")
    ha_light_names_str = obs.obs_data_get_string(settings, "ha_light_names")
    ha_light_names = ha_light_names_str.split('\n')

    if not ha_bearer_token.startswith('Bearer '):
        ha_bearer_token = 'Bearer ' + ha_bearer_token

    for i in range(len(ha_light_names)):
        ha_light_names[i] = ha_light_names[i].strip()
        # add 'light.' to the beginning of the light name if it's not already there
        if not ha_light_names[i].startswith('light.'):
            ha_light_names[i] = 'light.' + ha_light_names[i]

    source_name = obs.obs_data_get_string(settings, "source_name")
    filter_name = obs.obs_data_get_string(settings, "filter_name")
    sr_timer_template = obs.obs_data_get_string(settings, "sr_timer_template")
    turf_timer_template  = obs.obs_data_get_string(settings, "turf_timer_template")
    timer_301_template  = obs.obs_data_get_string(settings, "timer_301_template")
    rank_timer_template  = obs.obs_data_get_string(settings, "rank_timer_template")
    default_color   = obs.obs_data_get_int(settings, "default_color")

    device_id_str = obs.obs_data_get_string(settings, "device_list")

    video_capture_device_id = None
    if device_id_str.isnumeric():
        video_capture_device_id = int(device_id_str)

    if video_capture_device_id is None or source_name == "" or filter_name == "" or sr_timer_template == "" or turf_timer_template == "" or timer_301_template == "" or rank_timer_template == "":
        return

    sr_timer_cooldown = obs.obs_data_get_double(settings, "sr_timer_cooldown")
    turf_timer_cooldown = obs.obs_data_get_double(settings, "turf_timer_cooldown")
    timer_301_cooldown = obs.obs_data_get_double(settings, "timer_301_cooldown")
    rank_timer_cooldown = obs.obs_data_get_double(settings, "rank_timer_cooldown")

    sr_timer_confidence  = obs.obs_data_get_double(settings, "sr_timer_confidence")
    turf_timer_confidence  = obs.obs_data_get_double(settings, "turf_timer_confidence")
    timer_301_confidence  = obs.obs_data_get_double(settings, "timer_301_confidence")
    rank_timer_confidence  = obs.obs_data_get_double(settings, "rank_timer_confidence")
    
    templates = {}
    templates['SR_TIMER'] = ImgTemplate(sr_timer_template, 'SRTIMER', sr_timer_confidence, (31,31), 1000/update_interval * sr_timer_cooldown, on_sr_wave)
    templates['TURF_TIMER']  = ImgTemplate(turf_timer_template,'TURFTIMER', turf_timer_confidence, (303,17), 1000/update_interval * turf_timer_cooldown, on_300_timer)
    templates['TIMER_301']  = ImgTemplate(timer_301_template,'TIMER_301', timer_301_confidence, (304,17), 1000/update_interval * timer_301_cooldown, on_301_timer)
    templates['RANK_TIMER']  = ImgTemplate(rank_timer_template,'RANKTIMER', rank_timer_confidence, (304,16), 1000/update_interval * rank_timer_cooldown, on_battle)

    if vid is not None and last_device_id is not None and last_device_id != video_capture_device_id:
        vid.release()
        vid = None

    if vid is None:
        vid = cv2.VideoCapture(video_capture_device_id)
        if not vid.isOpened:
            print(f'\nCould not open video capture device index {video_capture_device_id:d}')
        else:
            print('Video Capture Device Opened')

    obs.timer_add(update_filter, update_interval)

    last_device_id = video_capture_device_id

def update_filter():
    global vid
    global frame_count
    global running
    global init_color

    if not running:
        return

    if frame_count == 0:
        r,g,b = int_to_rgb(default_color)
        update_filter_parameter(r/255.0, g/255.0, b/255.0,False)

    flag, frame  = vid.read()
    if flag:
        frame_gray = cv2.resize(frame, (640, 360), interpolation = cv2.INTER_AREA)
        frame_gray = cv2.cvtColor(frame_gray, cv2.COLOR_BGR2GRAY)
        frame_gray = frame_gray[:85, :]
        
        for temp in templates.values():
            temp.match(frame_count,frame,frame_gray)

        frame_count += 1


def script_cleanup():
    global vid
    if vid is not None:
        vid.release()
