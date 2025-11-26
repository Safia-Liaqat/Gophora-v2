import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import api, { APIURL } from '../../services/api.js'

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
        const res = await api.post(`/api/applications/apply?opportunity_id=${pendingAppId}`, {}, {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        });
        
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
      const response = await api.post('/api/auth/login', { 
        email: formData.email, 
        password: formData.password 
      });

      const data = response.data;
      
      // Calculate expiry time (24 hours from now)
      const expiryTime = Date.now() + (data.expires_in * 1000); // expires_in is in seconds
      
      // Save token, expiry time, and user data
      localStorage.setItem("token", data.access_token);
      localStorage.setItem("token_expiry", expiryTime.toString());
      localStorage.setItem("user", JSON.stringify(data.user));
      localStorage.setItem("role", data.user.role);

      // Check if the user's role matches the selected role
      if (data.user.role !== role) {
        setError(`This account is registered as a ${data.user.role}. Please select the correct role.`);
        localStorage.clear();
        return;
      }

      if (role === "seeker") {
        // Check for pending apps before navigating
        await handlePendingApplication(data.access_token);
        navigate("/seeker/dashboard");
      } else if (role === "provider") {
        navigate("/provider/dashboard");
      }

    } catch (err) {
      setError(err.response?.data?.detail || err.message || "Incorrect email or password");
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
