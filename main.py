from flask import Flask, render_template, request, redirect, url_for, session, jsonify
import json
import os
import subprocess
import threading
from datetime import datetime
import time

app = Flask(__name__)
app.secret_key = 'your_secret_key_here' # Doesn't need to be changed

TOKEN = "your_life360_token_here" # Follow the guide here to get yours: https://github.com/pnbruckner/ha-life360?tab=readme-ov-file#access-type--token
HEADERS = [
    "Authorization: Bearer " + TOKEN,
    "User-Agent: Life360/21.8.0 CFNetwork/1220.1 Darwin/20.3.0",
    "Accept: application/json",
    "Cache-Control: no-cache",
    "Accept-Language: en-US",
    "X-Life360-Client-Identifier: 12345678-1234-1234-1234-1234567890ab",
    "Cookie: _cfuvid=6rT1GYBoX_fa7hYvRnB.oMX0Zi_riuNfqqFhvwH60jA-1751407117597-0.0.1.1-604800000; __cf_bm=ur21pKl.Gs2aGPRNiW2p_FNOwNzR9STuvuemqw7pQVQ-1751407117-1.0.1.1-w4ve4OQX5WdzCiMVRFC0k11kHU4MdrSTIS6_J.fIPsBSAVmmG9Jo6Qq..xCVMsWhEr3R111nAcWh3DmvBVWrwnemii8p_tiS...HWXL2_UE"
]
INFO_FILE = "info.json"

# Get your own google maps API key from: https://developers.google.com/maps/documentation/javascript/get-api-key
GOOGLE_MAPS_API_KEY = "your_google_maps_token_here"

def curl_get(url):
    cmd = ["curl", "-k", "-s"]
    for header in HEADERS:
        cmd += ["-H", header]
    cmd.append(url)
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        return json.loads(result.stdout)
    except Exception as e:
        return {"error": str(e)}

def curl_post(url, data=""):
    cmd = ["curl", "-k", "-s", "-X", "POST"]
    for header in HEADERS:
        cmd += ["-H", header]
    if data:
        cmd += ["-d", data]
    cmd.append(url)
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        return json.loads(result.stdout)
    except Exception as e:
        return {"error": str(e)}

def load_info():
    if os.path.exists(INFO_FILE):
        with open(INFO_FILE, "r") as f:
            return json.load(f)
    return {"circles": {}, "members": {}}

def save_info(info):
    with open(INFO_FILE, "w") as f:
        json.dump(info, f, indent=2)

def update_circles_info(info, circles_data):
    updated = False
    for circle in circles_data.get("circles", []):
        cid = circle.get("id")
        name = circle.get("name")
        if cid and name and cid not in info["circles"]:
            info["circles"][cid] = name
            updated = True
    if updated:
        save_info(info)

def update_members_info(info, cid, members_data):
    updated = False
    if cid not in info["members"]:
        info["members"][cid] = {}
    for member in members_data.get("members", []):
        mid = member.get("id")
        fname = member.get("firstName", "")
        lname = member.get("lastName", "")
        name = f"{fname} {lname}".strip()
        if mid and name and mid not in info["members"][cid]:
            info["members"][cid][mid] = name
            updated = True
    if updated:
        save_info(info)

def get_member_locations(cid):
    url = f"https://api.life360.com/v3/circles/{cid}/members"
    data = curl_get(url)
    
    if 'error' in data:
        return []
    
    members = []
    for member in data.get('members', []):
        loc = member.get('location', {})
        members.append({
            'id': member.get('id'),
            'name': f"{member.get('firstName', '')} {member.get('lastName', '')}",
            'latitude': loc.get('latitude'),
            'longitude': loc.get('longitude'),
            'battery': loc.get('battery'),
            'address': loc.get('name') or loc.get('address1', ''),
            'timestamp': loc.get('timestamp'),
            'isDriving': loc.get('isDriving') == '1',
            'avatar': member.get('avatar'),
            'status': 'online' if member.get('features', {}).get('disconnected') == '0' else 'offline'
        })
    return members

@app.template_filter('timestamp_to_date')
def timestamp_to_date_filter(timestamp):
    try:
        if len(timestamp) > 10:
            timestamp = timestamp[:10]
        dt = datetime.fromtimestamp(int(timestamp))
        return dt.strftime('%Y-%m-%d %H:%M:%S')
    except:
        return timestamp

@app.template_filter('timestamp_to_datetime')
def timestamp_to_datetime_filter(timestamp):
    try:
        if len(timestamp) > 10:
            timestamp = timestamp[:10]
        dt = datetime.fromtimestamp(int(timestamp))
        return dt.strftime('%Y-%m-%d %H:%M:%S')
    except:
        return timestamp

@app.template_filter('timestamp_duration')
def timestamp_duration_filter(start, end):
    try:
        start_dt = datetime.fromtimestamp(int(start))
        end_dt = datetime.fromtimestamp(int(end))
        duration = end_dt - start_dt
        
        hours, remainder = divmod(duration.total_seconds(), 3600)
        minutes, seconds = divmod(remainder, 60)
        
        return f"{int(hours)}h {int(minutes)}m {int(seconds)}s"
    except:
        return "N/A"

@app.template_filter('pretty_json')
def pretty_json(value):
    return json.dumps(value, indent=2)

@app.route('/')
def index():
    return render_template('index.html', google_maps_key=GOOGLE_MAPS_API_KEY)

@app.route('/user_profile')
def user_profile():
    data = curl_get("https://api.life360.com/v3/users/me")
    return render_template('user_profile.html', user=data)

@app.route('/circles_list')
def circles_list():
    info = load_info()
    data = curl_get("https://api.life360.com/v4/circles")
    update_circles_info(info, data)
    return render_template('circles_list.html', circles=data.get('circles', []))

@app.route('/circle_details', methods=['GET', 'POST'])
def circle_details():
    info = load_info()
    
    if request.method == 'POST':
        cid = request.form.get('cid')
        if cid:
            session['selected_cid'] = cid
            return redirect(url_for('circle_details_result', cid=cid))
    
    return render_template('select_circle.html', 
                         circles=info.get("circles", {}), 
                         action_name="View Circle Details")

@app.route('/circle_details/<cid>')
def circle_details_result(cid):
    data = curl_get(f"https://api.life360.com/v3/circles/{cid}")
    return render_template('circle_details.html', circle=data)

@app.route('/circle_members', methods=['GET', 'POST'])
def circle_members():
    info = load_info()
    
    if request.method == 'POST':
        cid = request.form.get('cid')
        if cid:
            session['selected_cid'] = cid
            return redirect(url_for('circle_members_result', cid=cid))
    
    return render_template('select_circle.html', 
                         circles=info.get("circles", {}), 
                         action_name="View Circle Members")

@app.route('/circle_members/<cid>')
def circle_members_result(cid):
    data = curl_get(f"https://api.life360.com/v3/circles/{cid}/members")
    info = load_info()
    update_members_info(info, cid, data)
    return render_template('circle_members.html', members=data.get('members', []))

@app.route('/circle_map', methods=['GET', 'POST'])
def circle_map():
    info = load_info()
    
    if request.method == 'POST':
        cid = request.form.get('cid')
        if cid:
            session['selected_cid'] = cid
            return redirect(url_for('circle_map_view', cid=cid))
    
    return render_template('select_circle.html', 
                         circles=info.get("circles", {}), 
                         action_name="View Circle Map")

@app.route('/circle_map/<cid>')
def circle_map_view(cid):
    info = load_info()
    circle_name = info['circles'].get(cid, cid)
    return render_template('circle_map.html', cid=cid, circle_name=circle_name, google_maps_key=GOOGLE_MAPS_API_KEY)

@app.route('/api/circle_locations/<cid>')
def api_circle_locations(cid):
    locations = get_member_locations(cid)
    return jsonify(locations)

@app.route('/specific_member', methods=['GET', 'POST'])
def specific_member():
    info = load_info()
    
    if request.method == 'GET':
        return render_template('select_circle.html', 
                            circles=info.get("circles", {}), 
                            action_name="Select Member")
    
    if 'cid' in request.form:
        cid = request.form['cid']
        session['selected_cid'] = cid
        circle_name = info['circles'].get(cid, cid)
        members = info['members'].get(cid, {})
        return render_template('select_member.html', 
                             cid=cid, 
                             circle_name=circle_name, 
                             members=members)
    
    if 'mid' in request.form:
        cid = session.get('selected_cid', '')
        mid = request.form['mid']
        if cid and mid:
            return redirect(url_for('specific_member_result', cid=cid, mid=mid))
    
    return redirect(url_for('index'))

@app.route('/specific_member/<cid>/<mid>')
def specific_member_result(cid, mid):
    data = curl_get(f"https://api.life360.com/v3/circles/{cid}/members/{mid}")
    return render_template('specific_member.html', member=data)

if __name__ == '__main__':
    app.run(debug=True)
