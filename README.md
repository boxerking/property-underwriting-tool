# Indian Property Insurance Underwriting Tool

This Streamlit app helps property insurance underwriters assess risk at specific geographic locations across India.

## Features

- Interactive map centered on India with clickable property location selection
- Real-time elevation data from Open-Elevation API
- Flood risk classification based on elevation
- Urban flood risk zones for major Indian metro cities (Mumbai, Chennai, Kolkata, Delhi, Bengaluru)
- Fire brigade response time estimate based on sample fire stations in Indian cities
- Nearby properties exposure risk simulation
- Downloadable PDF report summarizing underwriting risk analysis

## Setup & Run

1. Clone the repo:
   ```
   git clone https://github.com/yourusername/indian-property-insurance-tool.git
   cd indian-property-insurance-tool
   ```

2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

3. Run the app locally:
   ```
   streamlit run app.py
   ```

## Deployment on Streamlit Cloud

1. Push your code to a GitHub repository.
2. Log in to [Streamlit Community Cloud](https://streamlit.io/cloud).
3. Create a new app, select your GitHub repo and branch.
4. Set main file path to `app.py`.
5. Deploy and share your app URL.

## Notes

- Urban flood zones and fire station locations are based on sample data; replace with official ISRO, NDMA, or municipal GIS data for production.
- Open-Elevation API is free and public but may have rate limits.
- Customize PDF reports and UI further to suit your organization’s requirements.

---

*Developed by [Your Name]*
