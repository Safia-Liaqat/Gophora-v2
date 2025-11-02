import React, { useState, useEffect } from "react";
import { APIURL } from '../../services/api.js'

export default function Profile() {
  const [profile, setProfile] = useState({
    name: "",
    email: "",
    skills: "",
    location: "",
  });

  const [editMode, setEditMode] = useState(false);

  useEffect(() => {
    const fetchProfileData = async () => {
      const token = localStorage.getItem("token");
      if (!token) {
        // Handle not logged in, maybe redirect to login
        return;
      }

      try {
        const [userRes, profileRes] = await Promise.all([
          fetch(`${APIURL}/api/users/me`, {
            headers: { Authorization: `Bearer ${token}` },
          }),
          fetch(`${APIURL}/api/profiles/me`, {
            headers: { Authorization: `Bearer ${token}` },
          }),
        ]);

        if (!userRes.ok || !profileRes.ok) {
          throw new Error("Failed to fetch profile data");
        }

        const userData = await userRes.json();
        const profileData = await profileRes.json();

        setProfile({
          name: userData.full_name || "",
          email: userData.email || "",
          skills: (profileData.skills || []).join(", "),
          location: [profileData.city, profileData.country]
            .filter(Boolean)
            .join(", "),
        });
      } catch (error) {
        console.error("Error fetching profile:", error);
        // Handle error, maybe show a notification to the user
      }
    };

    fetchProfileData();
  }, []);

  const handleChange = (e) =>
    setProfile({ ...profile, [e.target.name]: e.target.value });

  const handleSave = () => {
    // Send the updated profile data to the backend
    const token = localStorage.getItem("token");
    if (!token) {
      alert("You must be logged in to save your profile.");
      return;
    }

    // Build payload: convert skills string to array and split location into city/country
    const skillsArr = (profile.skills || "").split(",").map((s) => s.trim()).filter(Boolean);
    const locParts = (profile.location || "").split(",").map((p) => p.trim()).filter(Boolean);
    const city = locParts[0] || null;
    const country = locParts[1] || null;

    const payload = {
      skills: skillsArr,
    };
    if (city) payload.city = city;
    if (country) payload.country = country;

    fetch(`${APIURL}/api/profiles/me`, {
      method: "PUT",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify(payload),
    })
      .then(async (res) => {
        if (!res.ok) {
          const text = await res.text();
          throw new Error(text || "Failed to update profile");
        }
        return res.json();
      })
      .then((updatedProfile) => {
        setProfile((prev) => ({
          ...prev,
          skills: (updatedProfile.skills || []).join(", "),
          location: [updatedProfile.city, updatedProfile.country].filter(Boolean).join(", "),
        }));
        setEditMode(false);
        alert("Profile updated successfully!");

        // Optional: pre-warm recommendations so next view shows updated data immediately
        fetch(`${APIURL}/api/opportunities/recommend`, { headers: { Authorization: `Bearer ${token}` } }).catch(() => {});})
      .catch((err) => {
        console.error("Error updating profile:", err);
        alert("Failed to update profile. See console for details.");
      });
  };

  return (
    <div className="text-white">
      {/* 🌟 Heading */}
      <h2 className="text-3xl font-semibold mb-6 text-transparent bg-clip-text bg-gradient-to-r from-[#C5A3FF] to-[#9E7BFF] drop-shadow-[0_0_10px_rgba(158,123,255,0.6)]">
        My Profile
      </h2>

      {/* 🧩 Profile Card */}
      <div className="bg-[#161B30]/60 backdrop-blur-lg border border-[#2A2F55] p-8 rounded-2xl shadow-[0_0_25px_rgba(158,123,255,0.15)] max-w-lg mx-auto">
        <div className="space-y-5">
          {/* Name */}
          <div>
            <label className="block mb-2 font-medium text-[#C5A3FF]">
              Full Name
            </label>
            <input
              type="text"
              name="name"
              value={profile.name}
              onChange={handleChange}
              disabled={!editMode}
              className={`w-full p-3 rounded-xl border border-[#2A2F55] bg-[#0E1224] text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-[#9E7BFF] transition-all duration-200 ${
                !editMode ? "opacity-70 cursor-not-allowed" : ""
              }`}
            />
          </div>

          {/* Email */}
          <div>
            <label className="block mb-2 font-medium text-[#C5A3FF]">
              Email
            </label>
            <input
              type="email"
              name="email"
              value={profile.email}
              onChange={handleChange}
              disabled
              className={`w-full p-3 rounded-xl border border-[#2A2F55] bg-[#0E1224] text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-[#9E7BFF] transition-all duration-200 opacity-70 cursor-not-allowed`}
            />
          </div>

          {/* Skills */}
          <div>
            <label className="block mb-2 font-medium text-[#C5A3FF]">
              Skills
            </label>
            <input
              type="text"
              name="skills"
              value={profile.skills}
              onChange={handleChange}
              disabled={!editMode}
              className={`w-full p-3 rounded-xl border border-[#2A2F55] bg-[#0E1224] text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-[#9E7BFF] transition-all duration-200 ${
                !editMode ? "opacity-70 cursor-not-allowed" : ""
              }`}
            />
          </div>

          {/* Location */}
          <div>
            <label className="block mb-2 font-medium text-[#C5A3FF]">
              Location
            </label>
            <input
              type="text"
              name="location"
              value={profile.location}
              onChange={handleChange}
              disabled={!editMode}
              className={`w-full p-3 rounded-xl border border-[#2A2F55] bg-[#0E1224] text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-[#9E7BFF] transition-all duration-200 ${
                !editMode ? "opacity-70 cursor-not-allowed" : ""
              }`}
            />
          </div>
        </div>

        {/* Buttons */}
        <div className="mt-8">
          {!editMode ? (
            <button
              onClick={() => setEditMode(true)}
              className="w-full py-3 bg-gradient-to-r from-[#C5A3FF] to-[#9E7BFF] rounded-xl font-semibold hover:opacity-90 transition-all duration-200"
            >
              Edit Profile
            </button>
          ) : (
            <div className="flex gap-4">
              <button
                onClick={handleSave}
                className="flex-1 py-3 bg-gradient-to-r from-[#C5A3FF] to-[#9E7BFF] rounded-xl font-semibold hover:opacity-90 transition-all duration-200"
              >
                Save Changes
              </button>
              <button
                onClick={() => setEditMode(false)}
                className="flex-1 py-3 bg-gray-700 text-white rounded-xl font-semibold hover:bg-gray-600 transition-all duration-200"
              >
                Cancel
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
