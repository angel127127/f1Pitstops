import fastf1
from fastf1 import plotting
from matplotlib import pyplot as plt
import pandas as pd
import os
import numpy as np
import tkinter as tk
from tkinter import messagebox
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import logging

# setup logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logging.getLogger("fastf1").setLevel(logging.WARNING)

# Create the cache directory if it doesn't exist
cache_dir = 'cache'
if not os.path.exists(cache_dir):
    os.makedirs(cache_dir)

def extract(value):
    return value.get() if hasattr(value, "get") else value

# retrieves and filters data
def fetchData(gpYear, gpLocation):
    logging.info("Requesting telemetry: year = %s race = %s session = Q", gpYear, gpLocation)
    session = fastf1.get_session(gpYear, gpLocation, 'Q')
    session.load()
    logging.info("Session loaded, Drivers found = %s", list(session.results['Abbreviation']))

    results = session.results
    return session, results

# processes data, extracts features
def processData(session, results):
    q3_qualifiers = results[:10]
    top3_qual = results[:3]
    q3_drivers = q3_qualifiers['Abbreviation']
    top3_drivers = top3_qual['Abbreviation']

    fastest_lap = []
    na_drivers=[]
    telemetry_data = {}
    
    # create array of fastest quali times of top 10 drivers
    for _, driverRow in q3_qualifiers.iterrows():
        driver = driverRow['Abbreviation']
        lapTime = driverRow['Q3']
        logging.info("Processing Q3 lap for %s", driver)
        if pd.notna(lapTime):
            driverData = session.laps.pick_driver(driver)
            fastestLapData = driverData.loc[driverData['LapTime']==lapTime].iloc[0]
            fastest_lap.append({'Driver': driver, 'Fastest Lap (secs)': fastestLapData['LapTime'].total_seconds()})
        else:
            na_drivers.append(driver)
    fastest_lap.sort(key=lambda x: x['Fastest Lap (secs)'])# was otherwise sorted by grid position not laptime

    # create array of telemetry data for top 3 drivers
    for _, driverRow in top3_qual.iterrows():
        driver = driverRow['Abbreviation']
        lapTime = driverRow['Q3']
        logging.info("Processing podium driver lap for %s", driver)
        if pd.notna(lapTime):
            driverData = session.laps.pick_driver(driver)
            fastestLapData = driverData.loc[driverData['LapTime']==lapTime].iloc[0]
            telemetry = fastestLapData.get_telemetry()
            if telemetry is not None and not telemetry.empty:
                telemetry = telemetry.add_distance()
                telemetry_data[driver] = telemetry
            else:
                logging.warning("No telemetry found for %s", driver)


    # setup plotting
    df = pd.DataFrame(fastest_lap)
    df['TeamColour'] = ['#'+session.get_driver(d).TeamColor for d in df['Driver']]
    return df, fastest_lap, telemetry_data, na_drivers

def generateGraphs(session, df, fastest_lap, telemetry_data, na_drivers, gpLocation, gpYear, use_gui, root_widget):
    plotting.setup_mpl()

    if use_gui:
        # create a new window for the plots
        plot_window = tk.Toplevel(root_widget)
        plot_window.title(f"Qualifying Visualizations - {gpLocation} {gpYear}")
        plot_window.rowconfigure(0, weight=1)
        plot_window.columnconfigure(0, weight=1)
        plot_window.columnconfigure(1, weight=1)
        plot_window.columnconfigure(2, weight=1)
        fig1, ax1 = plt.subplots()
        fig2, ax2 = plt.subplots()
        fig3, ax3 = plt.subplots()
        combined_fig = None
    else:
        plot_window = None
        # setup for CLI graphs
        combined_fig, axs = plt.subplots(1,3, figsize=(18,6))
        ax1 = axs[0]
        ax2 = axs[1]
        ax3 = axs[2]
        fig1=fig2=fig3=combined_fig

    logging.info("Creating graphs")
    # create the first plot (speed vs distance)
    ax1.set_title(f'Speed vs Distance for Top Qualifiers')
    ax1.set_xlabel('Distance (m)')
    ax1.set_ylabel('Speed (km/h)')

    for driver in telemetry_data.keys():
      telemetry = telemetry_data[driver]
      colour = '#' + session.get_driver(driver).TeamColor
      ax1.plot(telemetry['Distance'], telemetry['Speed'], color=colour, label=driver)

    ax1.legend(title='Driver')

    if use_gui:
        # embed the first plot
        canvas1 = FigureCanvasTkAgg(fig1, master=plot_window)
        canvas1.draw()
        canvas1.get_tk_widget().grid(row=0, column=0, sticky="nsew", padx=10, pady=10)

    # create the second plot - fastest lap times
    ax2.bar(df['Driver'], df['Fastest Lap (secs)'], color=df['TeamColour'])
    ax2.set_xlabel('Driver')
    ax2.set_ylabel('Fastest Lap Time (seconds)')
    ax2.tick_params(axis='x', rotation=45)
    ax2.set_ylim(df['Fastest Lap (secs)'].min()-.2, df['Fastest Lap (secs)'].max()+.2)
    if na_drivers:
        naText = ",".join(na_drivers)
        boxText = f"Fastest Lap Times for Q3 Qualifiers\n\n{gpLocation} - {gpYear}\n\n(No Time Set in Q3: \n\n{naText})"
        ax2.set_title(boxText, fontsize=11, loc='center')
        plt.tight_layout(rect=[0,0,0.83,1])
    else:
        ax2.set_title(f'Fastest Lap Times for Q3 Qualifiers')
        plt.tight_layout()

    fig2.subplots_adjust(left=0.15)

    if use_gui:
        # embed the second plot
        fig2.subplots_adjust(left=0.15, top=0.85)
        canvas2 = FigureCanvasTkAgg(fig2, master=plot_window)
        canvas2.draw()
        canvas2.get_tk_widget().grid(row=0, column=1, sticky="nsew", padx=10, pady=10)

    for driver, tel in telemetry_data.items():
        colour = '#' + session.get_driver(driver).TeamColor
        ax3.plot(tel['Distance'], tel['Throttle'], label=f"{driver} Throttle", color=colour, alpha=0.9)
        ax3.plot(tel['Distance'], tel['Brake']*100, linestyle='--', label=f"{driver} Brake", color=colour, alpha=0.7)
    ax3.set_title(f"Throttle/Brake vs Distance - Top Qualifiers", fontsize=13)
    ax3.set_xlabel("Distance (m)")
    ax3.set_ylabel("Input %")
    ax3.grid(True)
    ax3.legend(loc='upper left', bbox_to_anchor=(1.02, 1), borderaxespad=0, fontsize=9, ncol=1)
    plt.tight_layout()
    #fig3.subplots_adjust(left=0.15)

    if use_gui:
        # embed third plot
        canvas3 = FigureCanvasTkAgg(fig3, master=plot_window)
        canvas3.draw()
        canvas3.get_tk_widget().grid(row=0, column=2, sticky="nsew", padx=10, pady=10)
    else:
        combined_fig.tight_layout()
        plt.show()

def getQualiData(gpLocation, gpYear, use_gui, root_widget=None):
  fastf1.Cache.enable_cache(cache_dir)
  # get data
  try:
    #set variables, get session data
    gpLocation = extract(gpLocation)
    gpYear = int(extract(gpYear))
    session, results = fetchData(gpYear, gpLocation)
    df, fastest_laps, telemetry_data, na_drivers = processData(session, results)
    generateGraphs(session, df, fastest_laps, telemetry_data, na_drivers, gpLocation, gpYear, use_gui, root_widget)

  except ValueError:
    messagebox.showinfo("Not valid race or year", "Please enter a valid race location and year.")
  except Exception as e:
    messagebox.showerror("Error", f"An error occurred: {e} in trying to access {gpLocation} {gpYear}")

if __name__ == "__main__":
    # set up tkinter widget
    root = tk.Tk()
    root.title("Qualifying visualisation tool")
    root.geometry("500x250")
    root.configure(bg="#1e1e1e")

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
    enterButton = tk.Button(inputFrame, text="Go", bg="#007acc", fg="white", activeforeground="blue", relief=tk.RAISED, bd=3, command=lambda: getQualiData(gpEntry, yearEntry, True, root)) # lambda to delay func call

    # placing attributes
    gpLabel.grid(row=0, column=0, padx=10, pady=10, sticky="w")
    gpEntry.grid(row=0, column=1, padx=10, pady=10, sticky="ew")
    yearLabel.grid(row=1, column=0, padx=10, pady=10, sticky="w")
    yearEntry.grid(row=1, column=1, padx=10, pady=10, sticky="ew")
    enterButton.grid(row=2, column=0, columnspan=2, pady=(20,5))

    root.mainloop()
