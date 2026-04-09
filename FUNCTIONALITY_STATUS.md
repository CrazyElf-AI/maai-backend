# MAAI 2.1 Website Status Report

Based on a codebase review of the frontend HTML files and the Flask (`app.py`) backend, here is a functional summary of the MAAI website.

## ✅ What is Functional (Working Correctly)

### 1. Navigation & Routing
- **Page Linking:** All internal navigation links between the main pages (`index.html`, `volunteer.html`, `ngo.html`, `Camps.html`, `our-team.html`, `login.html`, `ngo-register.html`, etc.) are correctly formatted and resolve properly. There are no broken `.html` references.
- **Dynamic Routing:** Links that pass query parameters, such as `initiative-details.html?id=...` and `login.html?tab=signup`, correctly parse and utilize the parameters on load.

### 2. Theming & Responsiveness
- **Dark/Light Mode:** The Tailwind CSS `dark:` class toggling works correctly using `localStorage` to persist the user's preference across pages.
- **Styling:** Custom CSS animations, gradients, glassmorphism (blur) effects, and layout grids are fully functional and responsive on both mobile and desktop views.

### 3. API Data Fetching (Read-Only)
The following public data endpoints correctly fetch data from the Flask API and dynamically render it into the DOM:
- **Initiatives:** Fetched from `/api/initiatives` and rendered on `ngo.html`, `volunteer.html`, etc.
- **Leadership/Mentors:** Fetched from `/api/leadership` and sorted by roles/categories.
- **Reels/Camps:** Fetched from `/api/reels` and `/api/camps`.
- **Testimonials:** Fetched from `/api/testimonials`.
- **Careers:** Fetched from `/api/careers`.

### 4. Authentication (Login & Signup)
- **Member Authentication:** The signup (`/member/signup`) and login (`/member/login`) flows on `login.html` successfully capture form data, send it to the backend, and store the JWT token in `localStorage`.
- **NGO Authentication:** The signup (`/ngo/signup`) and login (`/ngo/login`) flows on `ngo-register.html` successfully capture form data, send it to the backend, and store the JWT token.
- **Dashboards:** Both the NGO Dashboard and Member Portal (and Admin/Godmode portals) correctly attach the Authorization `Bearer` token to authenticated requests.

## 🛠️ Recently Fixed Issues

### 1. "Register Your Camp" Form Submission (`ngo.html`)
- **Resolved:** The camp proposal form now correctly checks for `localStorage.getItem('token')` before allowing submission. If no token is found, it clearly prompts the user to login. Additionally, it handles `401` and `403` API responses by throwing an explicit "Unauthorized. Please login to register a camp." error instead of a generic failure message.

### 2. Dark Mode Toggle Visual Desync (`ngo.html`)
- **Resolved:** The UI toggle switch now accurately syncs its visual on/off state to match the currently applied `dark` class mode on page load. 

### 3. Inconsistent API Base URLs
- **Resolved:** The frontend constants defining the backend URL (`API_BASE`) have been standardized globally across all HTML files. They now strictly use the base origin `https://maai-backend.onrender.com` (local) or `https://maai-backend.onrender.com` (production) and explicitly append `/api/` in individual `fetch()` route calls, reducing potential network and maintenance errors.

## ❌ What is NOT Functional (Bugs & Issues)

### 1. Hardcoded Statistics Animations
- **Issue:** In files like `ngo.html` and `volunteer.html`, the statistics counters (Camps Conducted, Beneficiaries Reached, etc.) animate to hardcoded values (e.g., 22, 800, 500, 17) rather than fetching live statistics from the backend database (like the `/api/admin/stats` endpoint).
- **Impact:** The public-facing stats will not update automatically as the database grows.
- **Fix Required:** Modify the `animateValue()` function calls to use values fetched dynamically from the API instead of hardcoded numbers.
