import axios from "axios";

const apiUrl = process.env.NEXT_PUBLIC_API_URL;

export const analyzeStock = async (ticker, startDate, endDate) => {
  try {
    const response = await axios.post(`${apiUrl}/analyze`, {
      ticker,
      start_date: startDate,
      end_date: endDate,
    });
    return response.data;
  } catch (err) {
    console.error("Backend error:", err.response?.data || err.message);
    throw err;
  }
};
