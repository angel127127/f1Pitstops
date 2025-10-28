import fastf1
from fastf1 import plotting
from matplotlib import pyplot as plt
import pandas as pd
import os
import numpy as np
import tkinter as tk
from tkinter import messagebox
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

# set up tkinter widget
root = tk.Tk()
root.title("Qualifying visualisation tool")
root.geometry("500x250")
root.configure(bg="#1e1e1e")

# Create the cache directory if it doesn't exist
cache_dir = 'cache'
if not os.path.exists(cache_dir):
    os.makedirs(cache_dir)

def getQualiData(gpLocation, gpYear):
  fastf1.Cache.enable_cache(cache_dir)
  # get data
  try:
    #set variables, get session data
    gpYear = gpYear.get()
    gpLocation = gpLocation.get()
    gpYear = int(gpYear)
    session = fastf1.get_session(gpYear, gpLocation, 'Q')
    session.load()

    results = session.results
    q3_qualifiers = results[:10]
    top3_qual = results[:3]
    q3_drivers = q3_qualifiers['Abbreviation']
    top3_drivers = top3_qual['Abbreviation']

#    print("Q3 Qualifiers: ", q3_drivers) test data

    fastest_lap = []
    telemetry_data = {}
    
    # create array of fastest quali times of top 10 drivers
    for driver in q3_drivers:
      driverData = session.laps.pick_driver(driver)
      fastestLapData = driverData.pick_fastest()
      fastest_lap.append({'Driver': driver, 'Fastest Lap (secs)': fastestLapData['LapTime'].total_seconds()})
    fastest_lap.sort(key=lambda x: x['Fastest Lap (secs)'])# was otherwise sorted by grid position not laptime

    # create array of telemetry data for top 3 drivers
    for driver in top3_drivers:
      driverData = session.laps.pick_driver(driver)
      fastestLapData = driverData.pick_fastest()
      telemetry = fastestLapData.get_telemetry()
      telemetry = telemetry.add_distance()
      telemetry_data[driver] = telemetry

    # setup plotting
    df = pd.DataFrame(fastest_lap)
    df['TeamColour'] = ['#'+session.get_driver(d).TeamColor for d in df['Driver']]

    plotting.setup_mpl()

    # create a new window for the plots
    plot_window = tk.Toplevel(root)
    plot_window.title(f"Qualifying Visualizations - {gpLocation} {gpYear}")
    plot_window.rowconfigure(0, weight=1)
    plot_window.columnconfigure(0, weight=1)
    plot_window.columnconfigure(1, weight=1)

    # create the first plot (speed vs distance)
    fig1, ax1 = plt.subplots()
    ax1.set_title(f'Speed vs Distance for Top Qualifiers in {gpLocation} {gpYear}')
    ax1.set_xlabel('Distance (meters)')
    ax1.set_ylabel('Speed (km/h)')

    for driver in top3_drivers:
      telemetry = telemetry_data[driver]
      colour = '#' + session.get_driver(driver).TeamColor
      ax1.plot(telemetry['Distance'], telemetry['Speed'], color=colour, label=driver)

    ax1.legend(title='Driver')

    # embed the first plot
    canvas1 = FigureCanvasTkAgg(fig1, master=plot_window)
    canvas1.draw()
    canvas1.get_tk_widget().grid(row=0, column=0, sticky="nsew", padx=10, pady=10)

    # create the second plot - fastest lap times
    fig2, ax2 = plt.subplots()
    ax2.bar(df['Driver'], df['Fastest Lap (secs)'], color=df['TeamColour'])
    ax2.set_xlabel('Driver')
    ax2.set_ylabel('Fastest Lap Time (seconds)')
    ax2.set_title(f'Fastest Lap Times for Q3 Qualifiers in {gpLocation} {gpYear}')
    ax2.tick_params(axis='x', rotation=45)
    ax2.set_ylim(df['Fastest Lap (secs)'].min()-.2, df['Fastest Lap (secs)'].max()+.2)

    # embed the second plot
    canvas2 = FigureCanvasTkAgg(fig2, master=plot_window)
    canvas2.draw()
    canvas2.get_tk_widget().grid(row=0, column=1, sticky="nsew", padx=10, pady=10)

  except ValueError:
    messagebox.showinfo("Not valid race or year", "Please enter a valid race location and year.")
  except Exception as e:
    messagebox.showerror("Error", f"An error occurred: {e} in trying to access {gpLocation} {gpYear}")

# frame for inputs
titleLabel = tk.Label(root, text="F1 Qualifying Visualisation Tool", font=("Helvetica", 16, "bold"), fg="#007acc", bg="#1e1e1e", pady=10)
inputFrame = tk.Frame(root, bg="#2b2b2b", padx=20, pady=20, relief=tk.RIDGE)
titleLabel.pack(pady=(20,10), fill="x")
inputFrame.pack(pady=10, fill="x", expand=True)
inputFrame.grid_columnconfigure(1, weight=1)

# attributes of main widget
gpLabel = tk.Label(inputFrame, text="Grand Prix: ", fg="white", bg="#2b2b2b")
gpEntry = tk.Entry(inputFrame, width=20, relief=tk.GROOVE)
yearLabel = tk.Label(inputFrame, text="Year: ", fg="white", bg="#2b2b2b")
yearEntry = tk.Entry(inputFrame, width = 20, relief=tk.GROOVE)
enterButton = tk.Button(inputFrame, text="Go", bg="#007acc", fg="white", activeforeground="blue", relief=tk.RAISED, bd=3, command=lambda: getQualiData(gpEntry, yearEntry)) # lambda to delay func call

# placing attributes
gpLabel.grid(row=0, column=0, padx=10, pady=10, sticky="w")
gpEntry.grid(row=0, column=1, padx=10, pady=10, sticky="ew")
yearLabel.grid(row=1, column=0, padx=10, pady=10, sticky="w")
yearEntry.grid(row=1, column=1, padx=10, pady=10, sticky="ew")
enterButton.grid(row=2, column=0, columnspan=2, pady=(20,5))

root.mainloop()
