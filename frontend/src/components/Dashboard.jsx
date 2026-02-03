import React, { useState, useEffect, useCallback } from 'react';
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
  const [exportingCSV, setExportingCSV] = useState(null);
  const [exportingPDF, setExportingPDF] = useState(null);

  const getAuthHeaders = () => {
    const token = localStorage.getItem('access_token');
    return {
      Authorization: `Bearer ${token}`,
    };
  };

  const loadDatasetById = async (dataset) => {
    try {
      // Method 1: Try new dedicated dataset endpoint (preferred)
      try {
        console.log(`Fetching /api/dataset/${dataset.id}/`);
        const response = await axios.get(`${API_URL}/api/dataset/${dataset.id}/`, {
          headers: getAuthHeaders(),
          timeout: 8000,
        });

        if (response.data && response.data.summary && response.data.raw_data) {
          console.log(`Dataset endpoint success: ${response.data.raw_data.length} rows loaded`);
          setSummary(response.data.summary);
          setRawData(response.data.raw_data);
          setCurrentDatasetId(dataset.id);
          setError('');
          return;
        } else {
          console.warn('Dataset endpoint returned incomplete data');
        }
      } catch (datasetError) {
        console.warn(`Dataset endpoint failed (${datasetError.response?.status || 'Network'}):`, datasetError.message);
        
        // Method 2: Fallback to CSV export and parse
        try {
          console.log(`Fetching /api/export/csv/${dataset.id}/ as fallback`);
          const csvResponse = await axios.get(`${API_URL}/api/export/csv/${dataset.id}/`, {
            headers: getAuthHeaders(),
            responseType: 'text',
            timeout: 8000,
          });
          
          if (csvResponse.data && typeof csvResponse.data === 'string') {
            const lines = csvResponse.data.split('\n').filter(line => line.trim());
            if (lines.length > 1) {
              const headers = lines[0].split(',').map(h => h.trim());
              const parsedData = lines.slice(1).map(line => {
                const values = line.split(',');
                const row = {};
                headers.forEach((header, index) => {
                  row[header] = values[index]?.trim() || '';
                });
                return row;
              });

              console.log(`CSV fallback success: ${parsedData.length} rows parsed`);
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
              setError('');
              return;
            }
          }
        } catch (csvError) {
          console.warn(`CSV fallback failed:`, csvError.message);
        }
      }
      
      // Last resort: Load summary only with available data
      console.log(`Loading summary-only for dataset ${dataset.id}`);
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
      setError('Loaded summary statistics only. Detailed data unavailable.');
    } catch (err) {
      console.error('Failed to load dataset:', err);
      setError(`Failed to load dataset: ${err.message}`);
    }
  };

  const fetchData = useCallback(async () => {
    try {
      // Always fetch history first
      const historyRes = await axios.get(`${API_URL}/api/history/`, { headers: getAuthHeaders() });
      setHistory(historyRes.data.history);
      
      // Try to get latest summary
      try {
        const summaryRes = await axios.get(`${API_URL}/api/summary/latest/`, { headers: getAuthHeaders() });
        setSummary(summaryRes.data.summary);
        setRawData(summaryRes.data.raw_data || []);
        
        // Set current dataset ID to the latest (first in history)
        if (historyRes.data.history && historyRes.data.history.length > 0) {
          setCurrentDatasetId(historyRes.data.history[0].id);
        }
      } catch (summaryErr) {
        // If summary endpoint fails, automatically load the latest dataset
        if (summaryErr.response?.status === 404 || summaryErr.response?.status === 500) {
          console.log('Summary endpoint failed, loading latest dataset from history...');
          
          if (historyRes.data.history && historyRes.data.history.length > 0) {
            const latestDataset = historyRes.data.history[0];
            console.log('Auto-loading latest dataset:', latestDataset.name, 'ID:', latestDataset.id);
            setError(`Loading latest dataset: ${latestDataset.name}...`);
            
            // Use the same dual-fallback logic as handleHistoryClick
            await loadDatasetById(latestDataset);
            setError(''); // Clear loading message after successful load
          } else {
            setSummary(null);
            setRawData([]);
            setError('No datasets available. Please upload a CSV file to begin.');
          }
        } else {
          throw summaryErr; // Re-throw for other errors
        }
      }
    } catch (err) {
      console.error('fetchData error:', err);
      if (err.response?.status === 401) {
        onLogout();
      } else {
        setError('Failed to load data. Please try refreshing the page.');
      }
    } finally {
      setLoading(false);
    }
  }, [onLogout]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

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
      // Try with current dataset ID first, fallback to general endpoint
      const endpoint = currentDatasetId 
        ? `${API_URL}/api/export/csv/${currentDatasetId}/`
        : `${API_URL}/api/export/csv/`;
      
      const response = await axios.get(endpoint, {
        headers: getAuthHeaders(),
        responseType: 'blob',
        timeout: 15000,
      });

      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      const filename = summary?.name || `dataset_${currentDatasetId || 'latest'}`;
      link.setAttribute('download', `${filename}.csv`);
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
    } catch (err) {
      console.error('CSV export error:', err);
      if (err.response?.status === 404) {
        setError('Dataset not found for export');
      } else if (err.response?.status === 401) {
        setError('Authentication failed. Please login again.');
        onLogout();
      } else {
        setError(`CSV export failed: ${err.response?.data?.error || err.message}`);
      }
    }
  };

  const handleExportPDF = async () => {
    try {
      // Try with current dataset ID first, fallback to general endpoint
      const endpoint = currentDatasetId 
        ? `${API_URL}/api/report/pdf/${currentDatasetId}/`
        : `${API_URL}/api/report/pdf/`;
      
      const response = await axios.get(endpoint, {
        headers: getAuthHeaders(),
        responseType: 'blob',
        timeout: 20000, // PDF generation might take longer
      });

      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      const filename = summary?.name || `dataset_${currentDatasetId || 'latest'}`;
      link.setAttribute('download', `${filename}_report.pdf`);
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
    } catch (err) {
      console.error('PDF export error:', err);
      if (err.response?.status === 404) {
        setError('Dataset not found for PDF export');
      } else if (err.response?.status === 401) {
        setError('Authentication failed. Please login again.');
        onLogout();
      } else if (err.response?.status === 500) {
        setError('PDF generation failed on server. Please try again.');
      } else {
        setError(`PDF export failed: ${err.response?.data?.error || err.message}`);
      }
    }
  };

  const handleExportCSVById = async (datasetId, datasetName) => {
    setExportingCSV(datasetId);
    try {
      console.log(`Exporting CSV for dataset ${datasetId}...`);
      const response = await axios.get(`${API_URL}/api/export/csv/${datasetId}/`, {
        headers: getAuthHeaders(),
        responseType: 'blob',
        timeout: 15000,
      });

      // Check if response is valid
      if (!response.data || response.data.size === 0) {
        setError(`CSV export failed for "${datasetName}": Empty response from server`);
        console.error('CSV export returned empty blob');
        setExportingCSV(null);
        return;
      }

      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      const timestamp = new Date().getTime();
      link.setAttribute('download', `${datasetName}_${timestamp}.csv`);
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
      
      setError('');
      console.log(`CSV exported successfully for dataset ${datasetId}`);
    } catch (err) {
      console.error('CSV export by ID error:', err);
      let errorMsg = 'CSV export failed';
      
      if (err.response?.status === 404) {
        errorMsg = `Dataset "${datasetName}" (ID: ${datasetId}) not found on server`;
      } else if (err.response?.status === 401) {
        errorMsg = 'Authentication failed. Please login again.';
        setTimeout(() => onLogout(), 1000);
      } else if (err.response?.status === 500) {
        errorMsg = `Server error while exporting "${datasetName}". Please try again.`;
      } else if (err.message === 'Network Error') {
        errorMsg = `Network error: Cannot reach backend server. Check if ${API_URL} is accessible`;
      } else if (err.code === 'ECONNABORTED') {
        errorMsg = 'Export timeout: Server took too long to respond';
      } else {
        errorMsg = `Export failed for "${datasetName}": ${err.response?.data?.error || err.message}`;
      }
      
      setError(errorMsg);
    } finally {
      setExportingCSV(null);
    }
  };

  const handleExportPDFById = async (datasetId, datasetName) => {
    setExportingPDF(datasetId);
    try {
      console.log(`Generating PDF report for dataset ${datasetId}...`);
      const response = await axios.get(`${API_URL}/api/report/pdf/${datasetId}/`, {
        headers: getAuthHeaders(),
        responseType: 'blob',
        timeout: 30000, // PDF generation takes longer
      });

      // Check if response is valid
      if (!response.data || response.data.size === 0) {
        setError(`PDF export failed for "${datasetName}": Empty response from server`);
        console.error('PDF export returned empty blob');
        setExportingPDF(null);
        return;
      }

      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      const timestamp = new Date().getTime();
      link.setAttribute('download', `${datasetName}_report_${timestamp}.pdf`);
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
      
      setError('');
      console.log(`PDF exported successfully for dataset ${datasetId}`);
    } catch (err) {
      console.error('PDF export by ID error:', err);
      let errorMsg = 'PDF export failed';
      
      if (err.response?.status === 404) {
        errorMsg = `Dataset "${datasetName}" (ID: ${datasetId}) not found for PDF generation`;
      } else if (err.response?.status === 401) {
        errorMsg = 'Authentication failed. Please login again.';
        setTimeout(() => onLogout(), 1000);
      } else if (err.response?.status === 500) {
        errorMsg = `PDF generation failed on server for "${datasetName}". Please try again.`;
      } else if (err.message === 'Network Error') {
        errorMsg = `Network error: Cannot reach backend server. Check if ${API_URL} is accessible`;
      } else if (err.code === 'ECONNABORTED') {
        errorMsg = 'PDF generation timeout: Server took too long to respond';
      } else {
        errorMsg = `PDF export failed for "${datasetName}": ${err.response?.data?.error || err.message}`;
      }
      
      setError(errorMsg);
    } finally {
      setExportingPDF(null);
    }
  };

  const checkApiHealth = async () => {
    try {
      const response = await axios.get(`${API_URL}/api/health/`, { timeout: 5000 });
      return response.status === 200;
    } catch (err) {
      return false;
    }
  };

  const handleHistoryClick = async (dataset) => {
    setLoadingDataset(true);
    setError('');
    
    const maxRetries = 3;
    const retryDelay = 1500;
    
    console.log(`Loading dataset ${dataset.id}: ${dataset.name}`);
    
    for (let attempt = 1; attempt <= maxRetries; attempt++) {
      try {
        // Check API health first
        const isHealthy = await checkApiHealth();
        if (!isHealthy) {
          console.warn(`API health check failed (attempt ${attempt}/${maxRetries})`);
          setError(`API is not responding. Retrying... (${attempt}/${maxRetries})`);
          await new Promise(resolve => setTimeout(resolve, retryDelay));
          continue;
        }
        
        console.log(`Attempting to load dataset ${dataset.id} (attempt ${attempt}/${maxRetries})`);
        
        // Use the shared loadDatasetById function
        await loadDatasetById(dataset);
        setLoadingDataset(false);
        console.log(`Successfully loaded dataset ${dataset.id}`);
        return;
        
      } catch (err) {
        console.error(`Attempt ${attempt} failed:`, err.message);
        
        if (attempt === maxRetries) {
          setError(`Failed to load dataset after ${maxRetries} attempts. Please check your connection and try again.`);
          setLoadingDataset(false);
          return;
        }
        
        setError(`Loading dataset... (${attempt}/${maxRetries})`);
        await new Promise(resolve => setTimeout(resolve, retryDelay * attempt));
      }
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
          {error && (
            <div className="error-message" style={{ 
              backgroundColor: '#ff5252', 
              color: 'white', 
              padding: '15px', 
              borderRadius: '4px',
              marginBottom: '15px',
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center'
            }}>
              <span>{error}</span>
              <button 
                onClick={() => setError('')}
                style={{
                  background: 'rgba(255,255,255,0.3)',
                  border: 'none',
                  color: 'white',
                  cursor: 'pointer',
                  padding: '5px 10px',
                  borderRadius: '3px',
                  fontSize: '14px'
                }}
              >
                ✕
              </button>
            </div>
          )}
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
                        disabled={loadingDataset}
                        data-testid={`analyze-${item.id}`}
                        style={{ opacity: loadingDataset ? 0.6 : 1, cursor: loadingDataset ? 'not-allowed' : 'pointer' }}
                      >
                        {loadingDataset ? '⏳ Loading...' : '📊 View Analysis'}
                      </button>
                      <button 
                        className="btn-small btn-secondary" 
                        onClick={() => handleExportCSVById(item.id, item.name)}
                        disabled={exportingCSV === item.id}
                        data-testid={`export-csv-${item.id}`}
                        style={{ opacity: exportingCSV === item.id ? 0.6 : 1, cursor: exportingCSV === item.id ? 'not-allowed' : 'pointer' }}
                      >
                        {exportingCSV === item.id ? '⏳ Exporting...' : '📄 CSV'}
                      </button>
                      <button 
                        className="btn-small btn-secondary" 
                        onClick={() => handleExportPDFById(item.id, item.name)}
                        disabled={exportingPDF === item.id}
                        data-testid={`export-pdf-${item.id}`}
                        style={{ opacity: exportingPDF === item.id ? 0.6 : 1, cursor: exportingPDF === item.id ? 'not-allowed' : 'pointer' }}
                      >
                        {exportingPDF === item.id ? '⏳ Generating...' : '📑 PDF'}
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
