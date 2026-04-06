import { useState } from "react";
import parks from "./data/parks.json"; // import the parks data
import "./App.css"; // import the CSS file

function App() {
  const [selectedPark, setSelectedPark] = useState(null); // state to track selected park

  return (
    <div className="app-container">
      {/* Left panel: Parks list */}
      <div className="left-panel">
        <h2>National Parks</h2>
        {parks.map((park, index) => (
          <div
            key={index}
            onClick={() => setSelectedPark(park)}
            className={`park-item ${selectedPark === park ? "selected" : ""}`}
          >
            {park.fullName}
          </div>
        ))}
      </div>

      {/* Right panel: Park details */}
      <div className="right-panel">
        {selectedPark ? (
          <ParkDetails park={selectedPark} />
        ) : (
          <p>Select a park to see forecast</p>
        )}
      </div>
    </div>
  );
}

function ParkDetails({ park }) { // component to display park details and forecast
  return (
    <div>
      <h2>{park.fullName}</h2>
      <p><strong>{park.designation}</strong></p>

      {/* Extra park info */}
      <p><strong>Location:</strong> {park.states || "N/A"}</p>
      <p><strong>Coordinates:</strong> {park.latitude}, {park.longitude}</p>
      {park.description && <p>{park.description}</p>}
      {park.url && (
        <p>
          <a href={park.url} target="_blank" rel="noopener noreferrer">
            Visit Official Site
          </a>
        </p>
      )}

      {/* Forecast section */}
      <Forecast park={park} />
    </div>
  );
}

// Forecast cards
function Forecast({ park }) { // component to display the 3-day forecast
  const days = [1, 2, 3]; // assuming your JSON has day1, day2, day3 flattened fields

  return (
    <div>
      <h3>3-Day Forecast</h3>
      <div className="forecast-container">
        {days.map((day) => (
          <div key={day} className="forecast-card">
            <p>{park[`day${day}_date`] || "N/A"}</p>
            {park[`day${day}_icon`] && (
              <img
                src={`https:${park[`day${day}_icon`]}`}
                alt="weather"
                style={{ width: "50px", height: "50px" }}
              />
            )}
            <p>{park[`day${day}_condition`] || "N/A"}</p>
            <p>
              {park[`day${day}_high_f`] ?? "-"}°F / {park[`day${day}_low_f`] ?? "-"}°F
            </p>
            <p>
              {park[`day${day}_high_c`] ?? "-"}°C / {park[`day${day}_low_c`] ?? "-"}°C
            </p>
          </div>
        ))}
      </div>
    </div>
  );
}

export default App;