import React, { useState, useEffect } from "react";
import { ChevronDown } from "lucide-react";
import { useNavigate } from "react-router-dom";
import { APIURL } from '../../services/api.js'

export default function Opportunities() {
  const [opportunities, setOpportunities] = useState([]);
  const [selectedCategory, setSelectedCategory] = useState("");
  const [selectedLocation, setSelectedLocation] = useState("");
  const [appliedIds, setAppliedIds] = useState([]);
  const [error, setError] = useState("");
  const navigate = useNavigate();

  useEffect(() => {
    const fetchOpportunities = async () => {
      setError(""); // Clear previous errors at the start
      try {
        const token = localStorage.getItem("token");
        if (!token) {
          setError("You must be logged in to see recommendations.");
          return;
        }

        const response = await fetch(`${APIURL}/api/opportunities/recommend`, {
          headers: {
            Authorization: `Bearer ${token}`, // Only Authorization needed
          },
        });

        // --- MORE ROBUST ERROR HANDLING ---
        if (!response.ok) {
          let errorDetail = `Request failed with status ${response.status}`;
          try {
            // Attempt to parse the backend's JSON error response
            const errorData = await response.json();
            // Use the 'detail' field if it exists, otherwise stringify the whole object
            errorDetail = errorData.detail || JSON.stringify(errorData);
          } catch (jsonError) {
            // If response is not JSON or parsing fails, use the status text
            errorDetail = response.statusText || errorDetail;
            console.error("Could not parse error JSON:", jsonError);
          }
          throw new Error(errorDetail); // Throw the extracted or generated error message
        }
        // --- END MORE ROBUST ERROR HANDLING ---
        
        const data = await response.json();
        setOpportunities(Array.isArray(data) ? data : []); 

      } catch (err) {
        console.error("Fetch Error:", err); // Log the full error
        // Normalize error into a readable string for the UI
        const formatError = (e) => {
          try {
            if (!e) return "An unknown error occurred";
            if (typeof e === "string") return e;
            if (e instanceof Error) return e.message || e.toString();
            // Some backends return a plain object like { detail: '...' }
            if (typeof e === "object") {
              if (e.detail) return String(e.detail);
              if (e.message) return String(e.message);
              // fallback to JSON
              return JSON.stringify(e);
            }
            return String(e);
          } catch (formatErr) {
            return "An unknown error occurred";
          }
        };

        setError(formatError(err));
      }
    };
    fetchOpportunities();
  }, []); // Runs once on load

  // ... (handleApply function remains the same) ...
  const handleApply = async (id) => {
    if (appliedIds.includes(id)) return;
    setError(""); 

    try {
      const token = localStorage.getItem("token");

      if (!token) {
        localStorage.setItem("pending_application_id", id);
        navigate("/login");
        return; 
      }

      const res = await fetch(`${APIURL}/api/applications/apply?opportunity_id=${id}`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
      });

      if (!res.ok) {
        const data = await res.json().catch(() => ({}));
        throw new Error(data.detail || "Failed to apply to opportunity");
      }

      setAppliedIds((prev) => [...prev, id]);
      
      const key = "applicationsSentDelta";
      const current = parseInt(localStorage.getItem(key) || "0", 10);
      localStorage.setItem(key, String(current + 1));

    } catch (err) {
      setError(err.message || "Failed to apply");
    }
  };

  // Ensure opportunities is always treated as an array
  const safeOpportunities = Array.isArray(opportunities) ? opportunities : [];

  const availableLocations = [
    ...new Set(safeOpportunities.map((op) => op.location).filter(Boolean)),
  ];

  const filteredOpportunities = safeOpportunities.filter((op) => {
    const matchesCategory = selectedCategory ? op.type === selectedCategory : true;
    const matchesLocation = selectedLocation ? op.location === selectedLocation : true;
    return matchesCategory && matchesLocation;
  });

  const clearFilters = () => {
    setSelectedCategory("");
    setSelectedLocation("");
  };

  return (
    <div className="text-white">
      <h2 className="text-2xl font-semibold mb-6 text-transparent bg-clip-text bg-gradient-to-r from-[#C5A3FF] to-[#9E7BFF] drop-shadow-[0_0_10px_rgba(158,123,255,0.6)]">
        Recommended Opportunities
      </h2>

      {/* Show detailed error message */}
      {error && <p className="text-red-500 bg-red-500/10 p-3 rounded-lg mb-4">Error: {error}</p>}

      {/* Filters JSX */}
      <div className="flex flex-col md:flex-row gap-4 mb-8 max-w-3xl">
        {/* Category */}
        <div className="flex-1">
          <label className="block mb-2 font-medium text-gray-300">Select Category</label>
          <div className="relative">
            <select
              value={selectedCategory}
              onChange={(e) => setSelectedCategory(e.target.value)}
              className="border border-white/20 p-3 pr-10 rounded-xl w-full bg-[#161B30] text-white appearance-none focus:outline-none focus:ring-2 focus:ring-[#C5A3FF] transition-all duration-200"
            >
              <option value="">All Categories</option>
              <option value="job">Job</option>
              <option value="internship">Internship</option>
              <option value="hackathon">Hackathon</option>
              <option value="project">Project</option>
              <option value="collaboration">Collaboration</option>
              <option value="other">Other</option>
            </select>
            <ChevronDown
              size={18}
              className="absolute right-3 top-1/2 -translate-y-1/2 text-[#C5A3FF] pointer-events-none"
            />
          </div>
        </div>

        {/* Location */}
        <div className="flex-1">
          <label className="block mb-2 font-medium text-gray-300">Select Location</label>
          <div className="relative">
            <select
              value={selectedLocation}
              onChange={(e) => setSelectedLocation(e.target.value)}
              disabled={safeOpportunities.length === 0}
              className={`border border-white/20 p-3 pr-10 rounded-xl w-full bg-[#161B30] text-white appearance-none focus:outline-none focus:ring-2 focus:ring-[#C5A3FF] transition-all duration-200 ${
                safeOpportunities.length === 0 ? "opacity-60 cursor-not-allowed" : ""
              }`}
            >
              <option value="">All Locations</option>
              {availableLocations.map((loc) => (
                <option key={loc} value={loc} className="bg-[#161B30] text-white">
                  {loc}
                </option>
              ))}
            </select>
            <ChevronDown
              size={18}
              className="absolute right-3 top-1/2 -translate-y-1/2 text-[#C5A3FF] pointer-events-none"
            />
          </div>
        </div>

        {/* Clear Filters */}
        <div className="flex items-end">
          <button
            onClick={clearFilters}
            className="py-3 px-6 bg-white/10 border border-white/20 text-white rounded-xl hover:bg-white/20 transition-all duration-200"
          >
            Clear Filters
          </button>
        </div>
      </div>

      {/* No Results */}
      {filteredOpportunities.length === 0 && !error && (
        <p className="text-gray-400 p-4 text-center">No opportunities found for your profile. Try updating your skills!</p>
      )}

      {/* Opportunities Table */}
      {filteredOpportunities.length > 0 && (
        <div className="overflow-x-auto">
          <table className="min-w-full border border-white/10 rounded-2xl bg-white/5 backdrop-blur-lg shadow-[0_0_25px_rgba(158,123,255,0.2)] text-gray-200">
            <thead className="bg-white/10 text-[#C5A3FF] uppercase text-sm tracking-wide">
              <tr>
                <th className="py-3 px-4 text-left">Title</th>
                <th className="py-3 px-4 text-left">Type</th>
                <th className="py-3 px-4 text-left">Location</th>
                <th className="py-3 px-4 text-left">Tags</th>
                <th className="py-3 px-4 text-left">Action</th>
              </tr>
            </thead>
            <tbody>
              {filteredOpportunities.map((op) => (
                <tr
                  key={op.id}
                  className="border-t border-white/10 hover:bg-white/10 transition-all duration-200"
                >
                  <td className="py-3 px-4">{op.title}</td>
                  <td className="py-3 px-4 capitalize">{op.type}</td>
                  <td className="py-3 px-4">{op.location}</td>
                  <td className="py-3 px-4">{(op.tags || []).join(", ")}</td>
                  <td className="py-3 px-4">
                    <button
                      onClick={() => handleApply(op.id)}
                      disabled={appliedIds.includes(op.id)}
                      className={`py-2 px-4 rounded-xl font-semibold transition-all duration-200 ${
                        appliedIds.includes(op.id)
                          ? "bg-white/20 text-gray-400 cursor-not-allowed"
                          : "bg-gradient-to-r from-[#C5A3FF] to-[#9E7BFF] text-white hover:opacity-90"
                      }`}
                    >
                      {appliedIds.includes(op.id) ? "Applied" : "Apply"}
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}