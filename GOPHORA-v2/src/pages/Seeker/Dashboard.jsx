import React, { useState, useEffect } from "react";
import { Sparkles, Send, Stars } from "lucide-react";
import { MapContainer, TileLayer, Marker, Popup } from "react-leaflet";
import L from "leaflet";
import "leaflet/dist/leaflet.css";
import { useNavigate, useOutletContext } from "react-router-dom";
import { APIURL } from '../../services/api.js'

export default function SeekerDashboard() {
  const { applicationsSent, appliedIds, setAppliedIds, setApplicationsSent } = useOutletContext();
  const [stats, setStats] = useState({
    recommended: 0,
    newMatches: 0,
  });
  const [error, setError] = useState("");
  const [opportunities, setOpportunities] = useState([]);
  const [selectedOpp, setSelectedOpp] = useState(null);
  const navigate = useNavigate();

  // Colored icons for different opportunity types
  const icons = {
    job: L.icon({
      iconUrl: "data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' width='32' height='32'%3E%3Cpath d='M12 2C8.13 2 5 5.13 5 9c0 5.25 7 13 7 13s7-7.75 7-13c0-3.87-3.13-7-7-7zm0 9.5c-1.38 0-2.5-1.12-2.5-2.5s1.12-2.5 2.5-2.5 2.5 1.12 2.5 2.5-1.12 2.5-2.5 2.5z' fill='%233b82f6'/%3E%3C/svg%3E",
      iconSize: [32, 32],
      iconAnchor: [16, 32],
      popupAnchor: [0, -32],
    }),
    hobby: L.icon({
      iconUrl: "data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' width='32' height='32'%3E%3Cpath d='M12 2C8.13 2 5 5.13 5 9c0 5.25 7 13 7 13s7-7.75 7-13c0-3.87-3.13-7-7-7zm0 9.5c-1.38 0-2.5-1.12-2.5-2.5s1.12-2.5 2.5-2.5 2.5 1.12 2.5 2.5-1.12 2.5-2.5 2.5z' fill='%2322c55e'/%3E%3C/svg%3E",
      iconSize: [32, 32],
      iconAnchor: [16, 32],
      popupAnchor: [0, -32],
    }),
    education: L.icon({
      iconUrl: "data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' width='32' height='32'%3E%3Cpath d='M12 2C8.13 2 5 5.13 5 9c0 5.25 7 13 7 13s7-7.75 7-13c0-3.87-3.13-7-7-7zm0 9.5c-1.38 0-2.5-1.12-2.5-2.5s1.12-2.5 2.5-2.5 2.5 1.12 2.5 2.5-1.12 2.5-2.5 2.5z' fill='%23f97316'/%3E%3C/svg%3E",
      iconSize: [32, 32],
      iconAnchor: [16, 32],
      popupAnchor: [0, -32],
    }),
    internship: L.icon({
      iconUrl: "data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' width='32' height='32'%3E%3Cpath d='M12 2C8.13 2 5 5.13 5 9c0 5.25 7 13 7 13s7-7.75 7-13c0-3.87-3.13-7-7-7zm0 9.5c-1.38 0-2.5-1.12-2.5-2.5s1.12-2.5 2.5-2.5 2.5 1.12 2.5 2.5-1.12 2.5-2.5 2.5z' fill='%2338bdf8'/%3E%3C/svg%3E",
      iconSize: [32, 32],
      iconAnchor: [16, 32],
      popupAnchor: [0, -32],
    }),
    hackathon: L.icon({
      iconUrl: "data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' width='32' height='32'%3E%3Cpath d='M12 2C8.13 2 5 5.13 5 9c0 5.25 7 13 7 13s7-7.75 7-13c0-3.87-3.13-7-7-7zm0 9.5c-1.38 0-2.5-1.12-2.5-2.5s1.12-2.5 2.5-2.5 2.5 1.12 2.5 2.5-1.12 2.5-2.5 2.5z' fill='%23c084fc'/%3E%3C/svg%3E",
      iconSize: [32, 32],
      iconAnchor: [16, 32],
      popupAnchor: [0, -32],
    }),
    project: L.icon({
      iconUrl: "data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' width='32' height='32'%3E%3Cpath d='M12 2C8.13 2 5 5.13 5 9c0 5.25 7 13 7 13s7-7.75 7-13c0-3.87-3.13-7-7-7zm0 9.5c-1.38 0-2.5-1.12-2.5-2.5s1.12-2.5 2.5-2.5 2.5 1.12 2.5 2.5-1.12 2.5-2.5 2.5z' fill='%232dd4bf'/%3E%3C/svg%3E",
      iconSize: [32, 32],
      iconAnchor: [16, 32],
      popupAnchor: [0, -32],
    }),
    collaboration: L.icon({
      iconUrl: "data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' width='32' height='32'%3E%3Cpath d='M12 2C8.13 2 5 5.13 5 9c0 5.25 7 13 7 13s7-7.75 7-13c0-3.87-3.13-7-7-7zm0 9.5c-1.38 0-2.5-1.12-2.5-2.5s1.12-2.5 2.5-2.5 2.5 1.12 2.5 2.5-1.12 2.5-2.5 2.5z' fill='%23f472b6'/%3E%3C/svg%3E",
      iconSize: [32, 32],
      iconAnchor: [16, 32],
      popupAnchor: [0, -32],
    }),
  };

  useEffect(() => {
    const fetchDashboardData = async () => {
      try {
        const token = localStorage.getItem("token");
        if (!token) throw new Error("Authentication token not found.");

        const recRes = await fetch(`${APIURL}/api/opportunities/recommend`, {
          headers: { Authorization: `Bearer ${token}` },
        });

        if (recRes.ok) {
          const recs = await recRes.json();
          setOpportunities(recs);
          const recommendedCount = Array.isArray(recs) ? recs.length : 0;

          const lastVisited =
            localStorage.getItem("lastVisitedSeekerDashboard");
          const newMatchesCount = lastVisited
            ? recs.filter(
                (opp) => new Date(opp.createdAt) > new Date(lastVisited)
              ).length
            : recommendedCount;

          setStats((prev) => ({
            ...prev,
            recommended: recommendedCount,
            newMatches: newMatchesCount,
          }));
        }
      } catch (err) {
        setError(err.message);
      }
    };

    fetchDashboardData();

    return () => {
      localStorage.setItem(
        "lastVisitedSeekerDashboard",
        new Date().toISOString()
      );
    };
  }, []);

  const handleApply = async (id) =>
    {
        try {
            const token = localStorage.getItem("token");
            if (!token) throw new Error("Authentication token not found.");
    
            const response = await fetch(`${APIURL}/api/applications/apply?opportunity_id=${id}`, {
                method: "POST",
                headers: {
                    Authorization: `Bearer ${token}`,
                },
            });
    
            if (response.ok) {
                alert("Application submitted successfully!");
                setAppliedIds([...appliedIds, id]);
                setApplicationsSent(prev => prev + 1);
            } else {
                throw new Error("Failed to submit application.");
            }
        } catch (err) {
            setError(err.message);
        }
    };

  return (
    <div className="text-white">
      <h2 className="text-3xl font-semibold mb-3 text-transparent bg-clip-text bg-gradient-to-r from-[#C5A3FF] to-[#9E7BFF] drop-shadow-[0_0_10px_rgba(158,123,255,0.6)]">
        Welcome, Opportunity Seeker 🌱
      </h2>
      <p className="text-gray-300 mb-8">
        Explore new opportunities tailored to your skills and location.
      </p>

      {error && (
        <p className="text-red-500 bg-red-500/10 p-3 rounded-lg mb-4">{error}</p>
      )}

      <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
        {/* Recommended */}
        <div className="bg-white/10 backdrop-blur-lg border border-white/10 p-6 rounded-2xl shadow-[0_0_25px_rgba(158,123,255,0.2)]">
          <div className="flex justify-between items-center mb-3">
            <h3 className="text-lg font-semibold text-[#C5A3FF]">
              Recommended for You
            </h3>
            <Sparkles className="w-6 h-6 text-[#C5A3FF]" />
          </div>
          <p className="text-4xl font-bold text-white">{stats.recommended}</p>
        </div>

        {/* Applications Sent */}
        <div className="bg-white/10 backdrop-blur-lg border border-white/10 p-6 rounded-2xl shadow-[0_0_25px_rgba(158,123,255,0.2)]">
          <div className="flex justify-between items-center mb-3">
            <h3 className="text-lg font-semibold text-[#C5A3FF]">
              Applications Sent
            </h3>
            <Send className="w-6 h-6 text-[#C5A3FF]" />
          </div>
          <p className="text-4xl font-bold text-white">{applicationsSent}</p>
        </div>

        {/* New Matches */}
        <div className="bg-white/10 backdrop-blur-lg border border-white/10 p-6 rounded-2xl shadow-[0_0_25px_rgba(158,123,255,0.2)]">
          <div className="flex justify-between items-center mb-3">
            <h3 className="text-lg font-semibold text-[#C5A3FF]">New Matches</h3>
            <Stars className="w-6 h-6 text-[#C5A3FF]" />
          </div>
          <p className="text-4xl font-bold text-white">{stats.newMatches}</p>
        </div>
      </div>

      {/* MAP SECTION */}
      <div className="h-[450px] rounded-xl overflow-hidden relative mt-6">
        <MapContainer
          center={[30.3753, 69.3451]}
          zoom={3}
          scrollWheelZoom={true}
          style={{ width: "100%", height: "100%" }}
        >
          {/* Dark Blue Basemap */}
          <TileLayer
            url="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png"
            attribution='&copy; <a href="https://carto.com/">CARTO</a>'
          />

          {opportunities.filter(opp => opp.lat && opp.lng && opp.location !== 'Remote').map((opp) => (
            <Marker
              key={opp.id}
              position={[opp.lat, opp.lng]}
              icon={icons[opp.type]}
              eventHandlers={{
                click: () => {
                  navigate(`/opportunity/${opp.id}`);
                },
              }}
              riseOnHover
            >
              <Popup>
                <h3>{opp.title}</h3>
                <p>{opp.location}</p>
                                <button
                  onClick={() => handleApply(opp.id)}
                  disabled={appliedIds.includes(opp.id)}
                  className={`mt-2 py-2 px-4 rounded-xl font-semibold transition-all duration-200 ${
                    appliedIds.includes(opp.id)
                      ? "bg-white/20 text-gray-400 cursor-not-allowed"
                      : "bg-gradient-to-r from-[#C5A3FF] to-[#9E7BFF] text-white hover:opacity-90"
                  }`}
                >
                  {appliedIds.includes(opp.id) ? "Applied" : "Apply"}
                </button>
              </Popup>
            </Marker>
          ))}
        </MapContainer>
      </div>
    </div>
  );
}
