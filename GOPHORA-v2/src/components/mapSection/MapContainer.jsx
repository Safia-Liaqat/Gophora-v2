import React, { useEffect } from "react";
import { MapContainer, TileLayer, Marker, Popup } from "react-leaflet";
import "leaflet/dist/leaflet.css"; // important for styling
import L from "leaflet";
import { useNavigate } from "react-router-dom";
import "leaflet/dist/leaflet.css";


const dummyOpportunities = [
  {
    id: "1",
    title: "Frontend Internship - Remote",
    category: "job",
    city: "Lahore",
    country: "Pakistan",
    coords: [31.5204, 74.3587],
  },
  {
    id: "2",
    title: "AI Research Collaboration",
    category: "education",
    city: "Berlin",
    country: "Germany",
    coords: [52.52, 13.405],
  },
  {
    id: "3",
    title: "Hackathon - Build for Good",
    category: "hobby",
    city: "San Francisco",
    country: "USA",
    coords: [37.7749, -122.4194],
  },
];


function CustomMarkers({ opportunities, onClick }) {
  const map = useMap();


  useEffect(() => {
    map.eachLayer((layer) => {
      if (layer instanceof L.Marker) map.removeLayer(layer);
    });


    opportunities.forEach((opp) => {
      const color =
        opp.category === "education"
          ? "#22c55e" // green
          : opp.category === "job"
          ? "#3b82f6" // blue
          : "#f97316"; // orange


      const icon = L.divIcon({
        className: "",
        html: `
          <div class="relative flex items-center justify-center animate-pulse-smooth">
            <i class="fa-solid fa-location-dot" style="color:${color}; font-size:28px;"></i>
            <span class="absolute w-6 h-6 rounded-full blur-md opacity-50" style="background-color:${color}"></span>
          </div>
        `,
        iconSize: [28, 28],
        iconAnchor: [14, 28],
      });


      const marker = L.marker(opp.coords, { icon }).addTo(map);
      marker.on("click", () => onClick(opp.id));
    });
  }, [map, opportunities, onClick]);


  return null;
}


export default function MapSection() {
  const navigate = useNavigate();


  return (
    <div className="bg-[#161B30]/90 border border-[#1f254a] rounded-xl p-6 text-white">
      <h2 className="text-lg font-semibold mb-2">
        🌍 Opportunities Around the World
      </h2>


      <p className="text-gray-400 text-sm mb-4">
        Explore{" "}
        <span className="text-blue-400 font-medium">Jobs</span>,{" "}
        <span className="text-green-400 font-medium">Education</span>, and{" "}
        <span className="text-orange-400 font-medium">Hobby</span> opportunities.
      </p>


      <div className="relative h-[22rem] overflow-hidden rounded-lg border border-[#1f254a]">
        <MapContainer
          center={[20, 0]}
          zoom={2}
          scrollWheelZoom={false}
          className="h-full w-full rounded-lg"
        >
          <TileLayer
            url="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png"
            attribution='&copy; <a href="https://carto.com/">CARTO</a>'
          />
          <CustomMarkers
            opportunities={dummyOpportunities}
            onClick={(id) => navigate(`/opportunity/${id}`)}
          />
        </MapContainer>
      </div>
    </div>
  );
}




