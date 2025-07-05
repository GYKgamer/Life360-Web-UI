# Life360 API Client

A Simple Flask-based web application that interacts with the Life360 API to provide a user-friendly interface for managing circles, members, and locations.

![image](https://github.com/user-attachments/assets/d06dec4b-e377-473b-9ef6-73b9cd5fe79c)

## Features

- **User Profile**: View detailed information about your Life360 account
- **Circle Management**: 
  - List all your circles
  - View circle details and members
  - See real-time member locations on a map
- **Member Tracking**:
  - View detailed member information
  - Check battery status and location history
  - Send requests to members
- **Interactive Map**: Visualize member locations with status indicators
- **Responsive Design**: Works on desktop and mobile devices

## Prerequisites

Before you begin, ensure you have met the following requirements:

- Python 3.7+
- pip package manager
- Life360 account
- Google Maps API key (for map functionality)

## Installation

1. Clone the repository:
   ```
   git clone https://github.com/GYKgamer/Life360-Web-UI
   cd Life360-Web-UI
  2. Install the required dependencies:
     ```
     pip install flask requests
     ```
  3. Edit all the required information in main.py, when you open it up, you will have to change lines 12 and 25<br />
  ![image](https://github.com/user-attachments/assets/b93b30e1-c78d-466e-81d1-ce76954ff2a2)
     To get your Life360 token, follow the tutorial [here](https://github.com/pnbruckner/ha-life360?tab=readme-ov-file#access-type--token)<br />
     To get your FREE Google Maps api key, follow this tutorial [here](https://developers.google.com/maps/documentation/javascript/get-api-key)

4. Run main.py and open your web browser and go to <h3> 127.0.0.1:5000 </h3>

5. And that's all, you now have a webui
