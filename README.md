# OBS-Splatoon3-Color-Detection-Filter
OBS Python script that detects your team color from the game UI and updates a filter accordingly

## Setup

- Install obs-shaderfilter to OBS (https://obsproject.com/forum/resources/obs-shaderfilter.1736/)
- Install `Python 3.11` (Tested Version: https://www.python.org/downloads/release/python-3116/)
  - When installing, make sure "Add Python environment variables" is checked
- Install required Python packages
  - Navigate to the code directory you extracted
  - Hold shift and right-click and select "Open PowerShell window here"
  - In the PowerShell window, type: `python -m pip -r requirements.txt`
- Download a zip archive of the code using the green button above labeled "Code"
- Extract the zip to some place warm and cozy on your PC where it will get direct sunlight
- Add shader as a filter on the source you'd like to see change color
  - In OBS, in your Sources panel, right-click the source and select Filters
  - Click the plus (+) button below the Effect Filters list
  - Give it a name and remember it for a few minutes
  - In the right panel, with your new effect filter selected, check "Load shader text from file"
  - Click the Browse button beside the empty box labeled "Shader text file"
  - Navigate to the code directory you extracted and select `replace_hue.shader`
  - Move the slider labeled "Target Hue" until the chroma key color in your source is replaced with the values defined by the "To Red/Green/Blue" sliders
- Add the script to OBS
  - In OBS, open the Scripts dialogue box (Tools->Scripts)
  - Switch to the tab "Python Settings"
  - Browse to the location of `Python 3.11` on your PC. For example: `"C:/Users/Agent8/AppData/Local/Programs/Python/Python311"`
  - Navigate to the code directory you extracted and select `s3_obs_detect_color.py`
  - Set the parameters of the script:
    - Source Name: name of the source to which you added the obs-shaderfilter
    - Filter Name: name of said filter (I told you to remember it)
    - Video Capture Device (select the device capturing from your Nintendo Switch)
    - Set the template locations
      - SR Timer Template: `sr_timer.png`
      - Turf Timer Template: `turf_timer.png`
      - 3:01 Timer Template: `timer_301.png`
      - Ranked Timer Template: `ranked_timer.png`
    - Set the cooldowns for detecting each template (`20.00 seconds` is fine for all of them)
    - Set the confidence values for each template
      - SR Timer Confidence Value: `0.05`
      - Turf Timer Confidence Value: `0.02`
      - 3:01 Timer Confidence Value: `0.02`
      - Ranked Timer Confidence Value: `0.02`
    - Set the Default Color to whatever color you'd like your source to start with
    - Check the box labeled "Running" at the top of the parameters once every other parameter is correctly defined
- Close and reopen OBS to save your settings and reload the script
- Enjoy! (Optional)
