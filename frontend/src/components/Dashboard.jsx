import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { Chart as ChartJS, CategoryScale, LinearScale, BarElement, LineElement, PointElement, ArcElement, Title, Tooltip, Legend } from 'chart.js';
import { Bar, Line, Pie } from 'react-chartjs-2';

ChartJS.register(CategoryScale, LinearScale, BarElement, LineElement, PointElement, ArcElement, Title, Tooltip, Legend);

const API_URL = process.env.NODE_ENV === 'development' 
  ? 'http://localhost:8002' 
  : `${window.location.protocol}//${window.location.hostname}:8002`;

function Dashboard({ onLogout }) {
  const [summary, setSummary] = useState(null);
  const [rawData, setRawData] = useState([]);
  const [history, setHistory] = useState([]);
  const [selectedFile, setSelectedFile] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(true);

  const getAuthHeaders = () => {
    const token = localStorage.getItem('access_token');
    return {
      Authorization: `Bearer ${token}`,
    };
  };

  const fetchData = async () => {
    try {
      const [summaryRes, historyRes] = await Promise.all([
        axios.get(`${API_URL}/api/summary/latest/`, { headers: getAuthHeaders() }),
        axios.get(`${API_URL}/api/history/`, { headers: getAuthHeaders() }),
      ]);

      setSummary(summaryRes.data.summary);
      setRawData(summaryRes.data.raw_data || []);
      setHistory(historyRes.data.history);
    } catch (err) {
      if (err.response?.status === 404) {
        setSummary(null);
        setRawData([]);
      } else if (err.response?.status === 401) {
        onLogout();
      }
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  const handleFileChange = (e) => {
    setSelectedFile(e.target.files[0]);
    setError('');
  };

  const handleUpload = async () => {
    if (!selectedFile) {
      setError('Please select a file');
      return;
    }

    setUploading(true);
    setError('');

    const formData = new FormData();
    formData.append('file', selectedFile);
    formData.append('name', selectedFile.name);

    try {
      await axios.post(`${API_URL}/api/upload/`, formData, {
        headers: {
          ...getAuthHeaders(),
          'Content-Type': 'multipart/form-data',
        },
      });

      setSelectedFile(null);
      document.getElementById('file-input').value = '';
      await fetchData();
    } catch (err) {
      setError(err.response?.data?.error || 'Upload failed');
    } finally {
      setUploading(false);
    }
  };

  const handleExportCSV = async () => {
    try {
      const response = await axios.get(`${API_URL}/api/export/csv/`, {
        headers: getAuthHeaders(),
        responseType: 'blob',
      });

      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', 'dataset.csv');
      document.body.appendChild(link);
      link.click();
      link.remove();
    } catch (err) {
      setError('Export failed');
    }
  };

  const handleExportPDF = async () => {
    try {
      const response = await axios.get(`${API_URL}/api/report/pdf/`, {
        headers: getAuthHeaders(),
        responseType: 'blob',
      });

      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', 'report.pdf');
      document.body.appendChild(link);
      link.click();
      link.remove();
    } catch (err) {
      setError('PDF generation failed');
    }
  };

  if (loading) {
    return (
      <div className="loading-container">
        <div className="spinner"></div>
      </div>
    );
  }

  const equipmentTypeLabels = summary ? Object.keys(summary.equipment_type_distribution) : [];
  const equipmentTypeCounts = summary ? Object.values(summary.equipment_type_distribution) : [];

  const parameterData = rawData.slice(0, 20).map(item => ({
    name: item['Equipment Name'],
    flowrate: item.Flowrate,
    pressure: item.Pressure,
    temperature: item.Temperature,
  }));

  return (
    <div className="dashboard" data-testid="dashboard-container">
      <header className="dashboard-header">
        <div className="header-left">
          <h1>Chemical Equipment Visualizer</h1>
          <p>Analyze and monitor your equipment parameters</p>
        </div>
        <div className="header-right">
          {summary && (
            <>
              <button className="btn-secondary" onClick={handleExportCSV} data-testid="export-csv-button">
                📊 Export CSV
              </button>
              <button className="btn-secondary" onClick={handleExportPDF} data-testid="export-pdf-button">
                📄 Export PDF
              </button>
            </>
          )}
          <button className="btn-logout" onClick={onLogout} data-testid="logout-button">
            Logout
          </button>
        </div>
      </header>

      <div className="dashboard-content">
        <section className="upload-section">
          <h2>Upload CSV Data</h2>
          {error && <div className="error-message">{error}</div>}
          <div className="upload-form">
            <div className="file-input-wrapper">
              <input
                type="file"
                id="file-input"
                className="file-input"
                accept=".csv"
                onChange={handleFileChange}
                data-testid="file-upload-input"
              />
            </div>
            <button
              className="btn-upload"
              onClick={handleUpload}
              disabled={uploading || !selectedFile}
              data-testid="upload-button"
            >
              {uploading ? 'Uploading...' : 'Upload & Process'}
            </button>
          </div>
        </section>

        {summary ? (
          <>
            <section className="summary-cards">
              <div className="stat-card" data-testid="total-count-card">
                <div className="stat-label">Total Equipment</div>
                <div className="stat-value">{summary.total_equipment_count}</div>
              </div>
              <div className="stat-card" data-testid="avg-flowrate-card">
                <div className="stat-label">Avg Flowrate</div>
                <div className="stat-value">{summary.avg_flowrate.toFixed(2)}</div>
              </div>
              <div className="stat-card" data-testid="avg-pressure-card">
                <div className="stat-label">Avg Pressure</div>
                <div className="stat-value">{summary.avg_pressure.toFixed(2)}</div>
              </div>
              <div className="stat-card" data-testid="avg-temperature-card">
                <div className="stat-label">Avg Temperature</div>
                <div className="stat-value">{summary.avg_temperature.toFixed(2)}</div>
              </div>
            </section>

            <section className="charts-container">
              <div className="chart-card">
                <h3>Equipment Type Distribution</h3>
                <Pie
                  data={{
                    labels: equipmentTypeLabels,
                    datasets: [
                      {
                        data: equipmentTypeCounts,
                        backgroundColor: [
                          'rgba(79, 195, 247, 0.8)',
                          'rgba(102, 187, 106, 0.8)',
                          'rgba(255, 167, 38, 0.8)',
                          'rgba(239, 83, 80, 0.8)',
                          'rgba(171, 71, 188, 0.8)',
                        ],
                        borderColor: 'rgba(255, 255, 255, 0.2)',
                        borderWidth: 2,
                      },
                    ],
                  }}
                  options={{
                    responsive: true,
                    plugins: {
                      legend: { position: 'bottom', labels: { color: '#E0E0E0', font: { size: 12 } } },
                    },
                  }}
                />
              </div>

              <div className="chart-card">
                <h3>Parameter Comparison (First 20)</h3>
                <Bar
                  data={{
                    labels: parameterData.map((d) => d.name),
                    datasets: [
                      {
                        label: 'Flowrate',
                        data: parameterData.map((d) => d.flowrate),
                        backgroundColor: 'rgba(79, 195, 247, 0.7)',
                      },
                      {
                        label: 'Pressure',
                        data: parameterData.map((d) => d.pressure),
                        backgroundColor: 'rgba(102, 187, 106, 0.7)',
                      },
                      {
                        label: 'Temperature',
                        data: parameterData.map((d) => d.temperature),
                        backgroundColor: 'rgba(255, 167, 38, 0.7)',
                      },
                    ],
                  }}
                  options={{
                    responsive: true,
                    plugins: {
                      legend: { position: 'top', labels: { color: '#E0E0E0' } },
                    },
                    scales: {
                      x: { ticks: { color: '#B0BEC5', display: false } },
                      y: { ticks: { color: '#B0BEC5' } },
                    },
                  }}
                />
              </div>
            </section>

            <section className="data-table-section">
              <h3>Equipment Data (First 50 rows)</h3>
              <div className="table-wrapper">
                <table className="data-table" data-testid="data-table">
                  <thead>
                    <tr>
                      <th>Equipment Name</th>
                      <th>Equipment Type</th>
                      <th>Flowrate</th>
                      <th>Pressure</th>
                      <th>Temperature</th>
                    </tr>
                  </thead>
                  <tbody>
                    {rawData.slice(0, 50).map((row, idx) => (
                      <tr key={idx}>
                        <td>{row['Equipment Name']}</td>
                        <td>{row['Equipment Type']}</td>
                        <td>{row.Flowrate}</td>
                        <td>{row.Pressure}</td>
                        <td>{row.Temperature}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </section>
          </>
        ) : (
          <div className="empty-state">
            <div className="empty-state-icon">📊</div>
            <h3>No Data Available</h3>
            <p>Upload a CSV file to start analyzing your equipment data</p>
          </div>
        )}
      </div>
    </div>
  );
}

export default Dashboard;
