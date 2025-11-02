import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import { APIURL } from '../../services/api.js'

export default function LoginForm() {
  const [role, setRole] = useState("");
  const [formData, setFormData] = useState({
    email: "",
    password: "",
  });
  const [error, setError] = useState("");
  const navigate = useNavigate();

  const handleChange = (e) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
  };

  // --- NEW: Helper function to handle pending applications ---
  const handlePendingApplication = async (token) => {
    const pendingAppId = localStorage.getItem("pending_application_id");
    
    // Check if there is a pending application ID
    if (pendingAppId) {
      try {
        const res = await fetch(`${APIURL}/api/applications/apply?opportunity_id=${pendingAppId}`, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${token}`,
          },
        });
        
        if (!res.ok) {
          throw new Error("Failed to submit pending application after login.");
        }
        
        // Success! Increment the dashboard delta count
        const key = "applicationsSentDelta";
        const current = parseInt(localStorage.getItem(key) || "0", 10);
        localStorage.setItem(key, String(current + 1));
        
      } catch (err) {
        // Don't block navigation, just log the error
        console.error("Error submitting pending application:", err);
      } finally {
        // Clear the pending ID regardless of success or failure
        localStorage.removeItem("pending_application_id");
      }
    }
  };
  // --- END OF NEW FUNCTION ---

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");

    if (!role) {
      setError("Please select a role before logging in.");
      return;
    }

    try {
      const response = await fetch(`${APIURL}/api/auth/login`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ ...formData, username: formData.email, role }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || "Incorrect email or password");
      }

      const data = await response.json();
      localStorage.setItem("token", data.access_token);
      localStorage.setItem("role", role);

      if (role === "seeker") {
        // --- UPDATED: Check for pending apps before navigating ---
        await handlePendingApplication(data.access_token);
        navigate("/seeker/dashboard");
        // --- END OF UPDATE ---
      } else if (role === "provider") {
        navigate("/provider/dashboard");
      }

    } catch (err) {
      setError(err.message);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="flex flex-col gap-5">
       {error && (
        <div className="bg-red-500/20 border border-red-500 text-red-300 p-3 rounded-lg text-center">
          {error}
        </div>
      )}
      {/* Role Selection */}
      <div className="flex gap-3 mb-2">
        {["seeker", "provider"].map((r) => (
          <button
            key={r}
            type="button"
            onClick={() => setRole(r)}
            className={`flex-1 py-2 rounded-xl font-medium transition-all duration-300
              ${
                role === r
                  ? "bg-gradient-to-r from-[#7F4DFF] to-[#9E7BFF] text-white shadow-[0_0_20px_rgba(158,123,255,0.5)]"
                  : "bg-white/5 border border-white/10 text-gray-300 hover:bg-white/10"
              }`}
          >
            {r === "seeker" ? "Seeker" : "Provider"}
          </button>
        ))}
      </div>

      {/* Email */}
      <input
        type="email"
        name="email"
        value={formData.email}
        onChange={handleChange}
        placeholder="Email Address"
        required
        className="bg-white/5 border border-white/10 text-white placeholder-gray-400 
                   p-3 rounded-xl focus:outline-none focus:ring-2 
                   focus:ring-[#9E7BFF] transition-all duration-300"
      />

      {/* Password */}
      <input
        type="password"
        name="password"
        value={formData.password}
        onChange={handleChange}
        placeholder="Password"
        required
        className="bg-white/5 border border-white/10 text-white placeholder-gray-400 
                   p-3 rounded-xl focus:outline-none focus:ring-2 
                   focus:ring-[#9E7BFF] transition-all duration-300"
      />

      {/* Submit */}
      <button
        type="submit"
        className="w-full py-3 rounded-xl font-semibold text-white tracking-wide
                   bg-gradient-to-r from-[#7F4DFF] to-[#9E7BFF]
                   hover:shadow-[0_0_30px_rgba(158,123,255,0.6)]
                   transition-all duration-300"
      >
        Log In
      </button>
    </form>
  );
}
