import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { Chart as ChartJS, CategoryScale, LinearScale, BarElement, LineElement, PointElement, ArcElement, Title, Tooltip, Legend } from 'chart.js';
import { Bar, Line, Pie, Scatter } from 'react-chartjs-2';
import API_URL from '../api';

ChartJS.register(CategoryScale, LinearScale, BarElement, LineElement, PointElement, ArcElement, Title, Tooltip, Legend);

function Dashboard({ onLogout }) {
  const [summary, setSummary] = useState(null);
  const [rawData, setRawData] = useState([]);
  const [history, setHistory] = useState([]);
  const [selectedFile, setSelectedFile] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(true);
  const [currentDatasetId, setCurrentDatasetId] = useState(null);
  const [loadingDataset, setLoadingDataset] = useState(false);
  const [currentPage, setCurrentPage] = useState(0);
  const [currentHistoryPage, setCurrentHistoryPage] = useState(0);

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
      // Set current dataset ID to the latest (first in history)
      if (historyRes.data.history && historyRes.data.history.length > 0) {
        setCurrentDatasetId(historyRes.data.history[0].id);
      }
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
      const endpoint = currentDatasetId 
        ? `${API_URL}/api/export/csv/${currentDatasetId}/`
        : `${API_URL}/api/export/csv/`;
      
      const response = await axios.get(endpoint, {
        headers: getAuthHeaders(),
        responseType: 'blob',
      });

      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      const filename = summary?.name || 'dataset';
      link.setAttribute('download', `${filename}.csv`);
      document.body.appendChild(link);
      link.click();
      link.remove();
    } catch (err) {
      setError('Export failed');
    }
  };

  const handleExportPDF = async () => {
    try {
      const endpoint = currentDatasetId 
        ? `${API_URL}/api/report/pdf/${currentDatasetId}/`
        : `${API_URL}/api/report/pdf/`;
      
      const response = await axios.get(endpoint, {
        headers: getAuthHeaders(),
        responseType: 'blob',
      });

      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      const filename = summary?.name || 'report';
      link.setAttribute('download', `${filename}_report.pdf`);
      document.body.appendChild(link);
      link.click();
      link.remove();
    } catch (err) {
      setError('PDF generation failed');
    }
  };

  const handleExportCSVById = async (datasetId, datasetName) => {
    try {
      const response = await axios.get(`${API_URL}/api/export/csv/${datasetId}/`, {
        headers: getAuthHeaders(),
        responseType: 'blob',
      });

      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `${datasetName}.csv`);
      document.body.appendChild(link);
      link.click();
      link.remove();
    } catch (err) {
      setError('Export failed');
    }
  };

  const handleExportPDFById = async (datasetId, datasetName) => {
    try {
      const response = await axios.get(`${API_URL}/api/report/pdf/${datasetId}/`, {
        headers: getAuthHeaders(),
        responseType: 'blob',
      });

      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `${datasetName}_report.pdf`);
      document.body.appendChild(link);
      link.click();
      link.remove();
    } catch (err) {
      setError('PDF generation failed');
    }
  };

  const handleHistoryClick = async (dataset) => {
    setLoadingDataset(true);
    setError('');
    
    try {
      // Fetch the specific dataset's raw data
      const response = await axios.get(`${API_URL}/api/export/csv/${dataset.id}/`, {
        headers: getAuthHeaders(),
        responseType: 'text',
      });
      
      // Parse CSV to get raw data
      const lines = response.data.split('\n');
      const headers = lines[0].split(',');
      const parsedData = lines.slice(1).filter(line => line.trim()).map(line => {
        const values = line.split(',');
        return headers.reduce((obj, header, index) => {
          obj[header.trim()] = values[index]?.trim();
          return obj;
        }, {});
      });

      // Update summary and raw data with the selected dataset
      setSummary({
        total_equipment_count: dataset.total_equipment_count,
        avg_flowrate: dataset.avg_flowrate,
        avg_pressure: dataset.avg_pressure,
        avg_temperature: dataset.avg_temperature,
        equipment_type_distribution: dataset.equipment_type_distribution,
        name: dataset.name,
        id: dataset.id,
        upload_timestamp: dataset.upload_timestamp,
      });
      setRawData(parsedData);
      setCurrentDatasetId(dataset.id);
    } catch (err) {
      // If CSV fetch fails, just update summary without raw data
      setSummary({
        total_equipment_count: dataset.total_equipment_count,
        avg_flowrate: dataset.avg_flowrate,
        avg_pressure: dataset.avg_pressure,
        avg_temperature: dataset.avg_temperature,
        equipment_type_distribution: dataset.equipment_type_distribution,
        name: dataset.name,
        id: dataset.id,
        upload_timestamp: dataset.upload_timestamp,
      });
      setRawData([]);
      setCurrentDatasetId(dataset.id);
      setError('Failed to load full dataset. Showing summary only.');
    } finally {
      setLoadingDataset(false);
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

  // For parameter comparison - keep first 20 for readability
  const parameterData = rawData.slice(0, 20).map(item => ({
    name: item['Equipment Name'],
    flowrate: item.Flowrate,
    pressure: item.Pressure,
    temperature: item.Temperature,
  }));

  // For other charts - use all data
  const allFlowrateData = rawData.map(item => parseFloat(item.Flowrate));
  
  // Pagination for table
  const rowsPerPage = 50;
  const totalPages = Math.ceil(rawData.length / rowsPerPage);
  const startIndex = currentPage * rowsPerPage;
  const endIndex = startIndex + rowsPerPage;
  const paginatedData = rawData.slice(startIndex, endIndex);

  const handleNextPage = () => {
    if (currentPage < totalPages - 1) {
      setCurrentPage(currentPage + 1);
    }
  };

  const handlePrevPage = () => {
    if (currentPage > 0) {
      setCurrentPage(currentPage - 1);
    }
  };

  // Pagination for history
  const historyPerPage = 6;
  const totalHistoryPages = Math.ceil(history.length / historyPerPage);
  const historyStartIndex = currentHistoryPage * historyPerPage;
  const historyEndIndex = historyStartIndex + historyPerPage;
  const paginatedHistory = history.slice(historyStartIndex, historyEndIndex);

  const handleNextHistoryPage = () => {
    if (currentHistoryPage < totalHistoryPages - 1) {
      setCurrentHistoryPage(currentHistoryPage + 1);
    }
  };

  const handlePrevHistoryPage = () => {
    if (currentHistoryPage > 0) {
      setCurrentHistoryPage(currentHistoryPage - 1);
    }
  };

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
        {loadingDataset && (
          <div className="loading-overlay">
            <div className="loading-spinner">
              <div className="spinner"></div>
              <p>Loading dataset...</p>
            </div>
          </div>
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
            {/* Dataset Context Banner */}
            <section className="dataset-context">
              <div className="dataset-context-icon">📊</div>
              <div className="dataset-context-info">
                <div className="dataset-context-name">Dataset: {summary.name || 'Unknown'}</div>
                <div className="dataset-context-timestamp">
                  Uploaded: {summary.upload_timestamp || new Date().toLocaleString()}
                </div>
              </div>
              <div className="active-badge">● ACTIVE</div>
            </section>

            <section className="summary-cards">
              <div className="stat-card" data-testid="total-count-card">
                <div className="stat-label">Total Equipment</div>
                <div className="stat-value">{summary.total_equipment_count}</div>
              </div>
              <div className="stat-card" data-testid="avg-flowrate-card">
                <div className="stat-label">Avg Flowrate (L/min)</div>
                <div className="stat-value">{summary.avg_flowrate.toFixed(2)}</div>
              </div>
              <div className="stat-card" data-testid="avg-pressure-card">
                <div className="stat-label">Avg Pressure (psi)</div>
                <div className="stat-value">{summary.avg_pressure.toFixed(2)}</div>
              </div>
              <div className="stat-card" data-testid="avg-temperature-card">
                <div className="stat-label">Avg Temperature (°F)</div>
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
                        label: 'Flowrate (L/min)',
                        data: parameterData.map((d) => d.flowrate),
                        backgroundColor: 'rgba(79, 195, 247, 0.7)',
                      },
                      {
                        label: 'Pressure (psi)',
                        data: parameterData.map((d) => d.pressure),
                        backgroundColor: 'rgba(102, 187, 106, 0.7)',
                      },
                      {
                        label: 'Temperature (°F)',
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
                      y: { 
                        title: { display: true, text: 'Values', color: '#B0BEC5' },
                        ticks: { color: '#B0BEC5' } 
                      },
                    },
                  }}
                />
              </div>

              <div className="chart-card">
                <h3>Temperature vs Pressure Analysis (All Data)</h3>
                <Scatter
                  data={{
                    datasets: [
                      {
                        label: 'Operating Point',
                        data: rawData.map(item => ({
                          x: parseFloat(item.Temperature),
                          y: parseFloat(item.Pressure)
                        })),
                        backgroundColor: 'rgba(79, 195, 247, 0.7)',
                        pointRadius: 3,
                      },
                    ],
                  }}
                  options={{
                    responsive: true,
                    plugins: {
                      legend: { position: 'top', labels: { color: '#E0E0E0' } },
                      tooltip: {
                        callbacks: {
                          label: function(context) {
                            return `(Temp: ${context.parsed.x}, Pressure: ${context.parsed.y})`;
                          }
                        }
                      }
                    },
                    scales: {
                      x: { 
                        type: 'linear', 
                        position: 'bottom',
                        title: { display: true, text: 'Temperature (°F)', color: '#B0BEC5' },
                        ticks: { color: '#B0BEC5' } 
                      },
                      y: { 
                        title: { display: true, text: 'Pressure (psi)', color: '#B0BEC5' },
                        ticks: { color: '#B0BEC5' } 
                      },
                    },
                  }}
                />
              </div>

              <div className="chart-card">
                <h3>Flowrate Performance Trend (All Equipment)</h3>
                <Line
                  data={{
                    labels: rawData.map((item, idx) => idx + 1),
                    datasets: [
                      {
                        label: 'Flowrate (L/min)',
                        data: allFlowrateData,
                        fill: true,
                        backgroundColor: 'rgba(79, 195, 247, 0.3)',
                        borderColor: 'rgba(79, 195, 247, 1)',
                        tension: 0.1,
                        pointRadius: 0,
                      },
                    ],
                  }}
                  options={{
                    responsive: true,
                    plugins: {
                      legend: { display: false },
                    },
                    scales: {
                      x: { 
                        title: { display: true, text: 'Equipment Index', color: '#B0BEC5' },
                        ticks: { color: '#B0BEC5', maxTicksLimit: 20 } 
                      },
                      y: { 
                        title: { display: true, text: 'Flowrate (L/min)', color: '#B0BEC5' },
                        ticks: { color: '#B0BEC5' } 
                      },
                    },
                  }}
                />
              </div>
            </section>

            <section className="history-section">
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
                <h3>Upload History (Showing {historyStartIndex + 1}-{Math.min(historyEndIndex, history.length)} of {history.length})</h3>
                {totalHistoryPages > 1 && (
                  <div style={{ display: 'flex', gap: '10px', alignItems: 'center' }}>
                    <button 
                      className="btn-secondary" 
                      onClick={handlePrevHistoryPage} 
                      disabled={currentHistoryPage === 0}
                      style={{ opacity: currentHistoryPage === 0 ? 0.5 : 1, cursor: currentHistoryPage === 0 ? 'not-allowed' : 'pointer' }}
                    >
                      ← Previous
                    </button>
                    <span style={{ color: '#B0BEC5', fontSize: '0.9rem' }}>Page {currentHistoryPage + 1} of {totalHistoryPages}</span>
                    <button 
                      className="btn-secondary" 
                      onClick={handleNextHistoryPage} 
                      disabled={currentHistoryPage === totalHistoryPages - 1}
                      style={{ opacity: currentHistoryPage === totalHistoryPages - 1 ? 0.5 : 1, cursor: currentHistoryPage === totalHistoryPages - 1 ? 'not-allowed' : 'pointer' }}
                    >
                      Next →
                    </button>
                  </div>
                )}
              </div>
              <div className="history-cards">
                {paginatedHistory.map((item) => (
                  <div 
                    className={`history-card ${item.id === currentDatasetId ? 'active' : ''}`} 
                    key={item.id}
                  >
                    <div className="history-header">
                      <h4>{item.name} (ID: {item.id})</h4>
                      <div className="history-date">Uploaded on: {new Date(item.upload_timestamp).toLocaleString()}</div>
                    </div>
                    <div className="history-stats">
                      <div className="history-stat">
                        <span className="stat-label">Total Equipment</span>
                        <span className="stat-value">{item.total_equipment_count}</span>
                      </div>
                      <div className="history-stat">
                        <span className="stat-label">Avg Flowrate</span>
                        <span className="stat-value">{item.avg_flowrate} L/min</span>
                      </div>
                      <div className="history-stat">
                        <span className="stat-label">Avg Pressure</span>
                        <span className="stat-value">{item.avg_pressure} psi</span>
                      </div>
                      <div className="history-stat">
                        <span className="stat-label">Avg Temperature</span>
                        <span className="stat-value">{item.avg_temperature} °F</span>
                      </div>
                    </div>
                    <div className="history-actions">
                      <button 
                        className="btn-small btn-primary" 
                        onClick={() => handleHistoryClick(item)}
                        data-testid={`analyze-${item.id}`}
                      >
                        📊 View Analysis
                      </button>
                      <button 
                        className="btn-small btn-secondary" 
                        onClick={() => handleExportCSVById(item.id, item.name)}
                        data-testid={`export-csv-${item.id}`}
                      >
                        📄 CSV
                      </button>
                      <button 
                        className="btn-small btn-secondary" 
                        onClick={() => handleExportPDFById(item.id, item.name)}
                        data-testid={`export-pdf-${item.id}`}
                      >
                        📑 PDF
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            </section>

            <section className="data-table-section">
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
                <h3>Equipment Data (Showing {startIndex + 1}-{Math.min(endIndex, rawData.length)} of {rawData.length} rows)</h3>
                <div style={{ display: 'flex', gap: '10px', alignItems: 'center' }}>
                  <button 
                    className="btn-secondary" 
                    onClick={handlePrevPage} 
                    disabled={currentPage === 0}
                    style={{ opacity: currentPage === 0 ? 0.5 : 1, cursor: currentPage === 0 ? 'not-allowed' : 'pointer' }}
                  >
                    ← Previous
                  </button>
                  <span style={{ color: '#B0BEC5', fontSize: '0.9rem' }}>Page {currentPage + 1} of {totalPages}</span>
                  <button 
                    className="btn-secondary" 
                    onClick={handleNextPage} 
                    disabled={currentPage === totalPages - 1}
                    style={{ opacity: currentPage === totalPages - 1 ? 0.5 : 1, cursor: currentPage === totalPages - 1 ? 'not-allowed' : 'pointer' }}
                  >
                    Next →
                  </button>
                </div>
              </div>
              <div className="table-wrapper">
                <table className="data-table" data-testid="data-table">
                  <thead>
                    <tr>
                      <th>#</th>
                      <th>Equipment Name</th>
                      <th>Equipment Type</th>
                      <th>Flowrate (L/min)</th>
                      <th>Pressure (psi)</th>
                      <th>Temperature (°F)</th>
                    </tr>
                  </thead>
                  <tbody>
                    {paginatedData.map((row, idx) => (
                      <tr key={startIndex + idx}>
                        <td>{startIndex + idx + 1}</td>
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
