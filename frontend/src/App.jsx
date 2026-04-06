import { useState } from "react";
import parks from "/data/national_parks_weather.json";

function App() {
  const [selectedPark, setSelectedPark] = useState(null);

  return (
    <div style={{ display: "flex", height: "100vh", fontFamily: "Arial, sans-serif" }}>
      {/* Left panel: Parks list */}
      <div style={{ width: "30%", borderRight: "1px solid #ccc", padding: "10px", overflowY: "auto" }}>
        <h2>National Parks</h2>
        {parks.map((park, index) => (
          <div
            key={index}
            onClick={() => setSelectedPark(park)}
            style={{
              cursor: "pointer",
              padding: "8px",
              borderBottom: "1px solid #eee",
              backgroundColor: selectedPark === park ? "#f0f8ff" : "transparent",
            }}
          >
            {park.fullName}
          </div>
        ))}
      </div>

      {/* Right panel: Park details */}
      <div style={{ flex: 1, padding: "10px", overflowY: "auto" }}>
        {selectedPark ? (
          <ParkDetails park={selectedPark} />
        ) : (
          <p>Select a park to see forecast</p>
        )}
      </div>
    </div>
  );
}

// Component for park details + forecast
function ParkDetails({ park }) {
  return (
    <div>
      <h2>{park.fullName}</h2>
      <p><strong>{park.designation}</strong></p>
      <Forecast park={park} />
    </div>
  );
}

// Forecast cards
function Forecast({ park }) {
  const days = [1, 2, 3]; // assuming your JSON has day1, day2, day3 flattened fields

  return (
    <div>
      <h3>3-Day Forecast</h3>
      <div style={{ display: "flex", gap: "10px" }}>
        {days.map((day) => (
          <div
            key={day}
            style={{
              border: "1px solid #ccc",
              padding: "10px",
              borderRadius: "8px",
              width: "120px",
              textAlign: "center",
            }}
          >
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