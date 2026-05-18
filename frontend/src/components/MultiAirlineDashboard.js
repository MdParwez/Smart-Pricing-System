import React, { useCallback, useEffect, useRef, useState } from 'react';
import {
  Alert,
  Box,
  Button,
  Chip,
  CircularProgress,
  Container,
  Grid,
  Paper,
  Stack,
  Step,
  StepLabel,
  Stepper,
  TextField,
  Typography,
} from '@mui/material';
import AirlineSelection from './AirlineSelection';
import RouteSelection from './RouteSelection';
import FlightResults from './FlightResults';
import { scraperService } from '../services/scraperService';

const steps = ['Airline', 'Route', 'Dates', 'Results'];

const MultiAirlineDashboard = () => {
  const [step, setStep] = useState(0);
  const [selectedAirline, setSelectedAirline] = useState(null);
  const [selectedRoute, setSelectedRoute] = useState(null);
  const [reportName, setReportName] = useState('');
  const [startDate, setStartDate] = useState('');
  const [endDate, setEndDate] = useState('');
  const [includeCompetitors, setIncludeCompetitors] = useState(true);
  const [numPassengers, setNumPassengers] = useState(1);
  const [loading, setLoading] = useState(false);
  const [taskId, setTaskId] = useState(null);
  const [taskStatus, setTaskStatus] = useState(null);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const visualizationOpenedRef = useRef(false);

  useEffect(() => {
    if (!taskId || !['running', 'queued'].includes(taskStatus?.status)) return undefined;

    const interval = setInterval(async () => {
      try {
        const status = await scraperService.getScrapingStatus(taskId);
        setTaskStatus(status);
      } catch (err) {
        setError(`Failed to check task status: ${err.message}`);
      }
    }, 3000);

    return () => clearInterval(interval);
  }, [taskId, taskStatus?.status]);

  useEffect(() => {
    if (
      taskStatus?.status === 'completed'
      && taskStatus?.output_filename
      && !visualizationOpenedRef.current
    ) {
      visualizationOpenedRef.current = true;
      const file = encodeURIComponent(taskStatus.output_filename);
      window.location.href = `/fare_intelligence.html?file=${file}`;
    }
  }, [taskStatus?.status, taskStatus?.output_filename]);

  const resetMessages = () => {
    setError('');
    setSuccess('');
  };

  const handleAirlineSelect = useCallback((airline) => {
    resetMessages();
    setSelectedAirline(airline);
    setSelectedRoute(null);
  }, []);

  const handleRouteSelect = useCallback((route) => {
    setSelectedRoute(route);
  }, []);

  const handleStartScraping = async () => {
    resetMessages();

    if (!reportName.trim()) {
      setError('Please enter a report name.');
      return;
    }
    if (!selectedAirline) {
      setError('Please select an airline.');
      return;
    }
    if (!selectedRoute) {
      setError('Please select a route.');
      return;
    }
    if (!startDate) {
      setError('Please select a start date.');
      return;
    }

    try {
      setLoading(true);
      const payload = {
        reportName: reportName.trim(),
        airline: selectedAirline.airline,
        origin: selectedRoute.origin,
        destination: selectedRoute.destination,
        startDate,
        endDate: endDate || startDate,
        numPassengers,
        includeCompetitors,
        currency: 'EUR',
        channel: 'playwright',
      };

      const response = await scraperService.startMultiAirlineScrape(payload);
      visualizationOpenedRef.current = false;
      setTaskId(response.task_id);
      setTaskStatus({ status: 'running', progress: 0, records_count: 0, airlines_scraped: [] });
      setSuccess('Scraping started successfully.');
      setStep(3);
    } catch (err) {
      setError(`Failed to start scraping: ${err.response?.data?.detail || err.message}`);
    } finally {
      setLoading(false);
    }
  };

  const resetForm = () => {
    setStep(0);
    setSelectedAirline(null);
    setSelectedRoute(null);
    setReportName('');
    setStartDate('');
    setEndDate('');
    setIncludeCompetitors(true);
    setNumPassengers(1);
    setTaskId(null);
    setTaskStatus(null);
    resetMessages();
  };

  return (
    <Container maxWidth="lg" sx={{ py: 4 }}>
      <Stack spacing={3}>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', gap: 2, alignItems: 'center' }}>
          <Box>
            <Typography variant="h4" fontWeight={700}>
              Multi-Airline Flight Scraper
            </Typography>
            <Typography color="text.secondary">
              Compare fares across a selected airline and configured competitors.
            </Typography>
          </Box>
          <Button variant="outlined" href="/">
            Standard Scraper
          </Button>
        </Box>

        <Paper elevation={2} sx={{ p: 3 }}>
          <Stepper activeStep={step} alternativeLabel>
            {steps.map((label) => (
              <Step key={label}>
                <StepLabel>{label}</StepLabel>
              </Step>
            ))}
          </Stepper>
        </Paper>

        {error && <Alert severity="error">{error}</Alert>}
        {success && <Alert severity="success">{success}</Alert>}

        {step === 0 && (
          <Stack spacing={2}>
            <AirlineSelection
              onAirlineSelect={handleAirlineSelect}
              onCompetitorsChange={setIncludeCompetitors}
            />
            <Box sx={{ display: 'flex', justifyContent: 'flex-end' }}>
              <Button
                variant="contained"
                onClick={() => {
                  if (!selectedAirline) {
                    setError('Please select an airline first.');
                    return;
                  }
                  resetMessages();
                  setStep(1);
                }}
              >
                Continue
              </Button>
            </Box>
          </Stack>
        )}

        {step === 1 && selectedAirline && (
          <Stack spacing={2}>
            <RouteSelection airline={selectedAirline} onRouteSelect={handleRouteSelect} />
            <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
              <Button onClick={() => setStep(0)}>Back</Button>
              <Button
                variant="contained"
                onClick={() => {
                  if (!selectedRoute) {
                    setError('Please select a route first.');
                    return;
                  }
                  resetMessages();
                  setStep(2);
                }}
              >
                Continue
              </Button>
            </Box>
          </Stack>
        )}

        {step === 2 && (
          <Paper elevation={2} sx={{ p: 3 }}>
            <Stack spacing={3}>
              <Typography variant="h5" fontWeight={600}>
                Set Dates and Details
              </Typography>

              <TextField
                fullWidth
                label="Report Name"
                placeholder="Ryanair_Dublin_June"
                value={reportName}
                onChange={(event) => setReportName(event.target.value)}
              />

              <Grid container spacing={2}>
                <Grid item xs={12} md={4}>
                  <TextField
                    fullWidth
                    type="date"
                    label="Start Date"
                    value={startDate}
                    onChange={(event) => setStartDate(event.target.value)}
                    InputLabelProps={{ shrink: true }}
                  />
                </Grid>
                <Grid item xs={12} md={4}>
                  <TextField
                    fullWidth
                    type="date"
                    label="End Date"
                    value={endDate}
                    onChange={(event) => setEndDate(event.target.value)}
                    InputLabelProps={{ shrink: true }}
                  />
                </Grid>
                <Grid item xs={12} md={4}>
                  <TextField
                    fullWidth
                    type="number"
                    label="Passengers"
                    value={numPassengers}
                    onChange={(event) => {
                      const value = Number.parseInt(event.target.value, 10);
                      setNumPassengers(Number.isNaN(value) ? 1 : Math.min(Math.max(value, 1), 9));
                    }}
                    inputProps={{ min: 1, max: 9 }}
                  />
                </Grid>
              </Grid>

              <Paper variant="outlined" sx={{ p: 2, bgcolor: 'grey.50' }}>
                <Stack direction="row" spacing={1} useFlexGap flexWrap="wrap">
                  <Chip label={`Airline: ${selectedAirline?.airline || '-'}`} />
                  <Chip label={`Route: ${selectedRoute?.origin || '-'} to ${selectedRoute?.destination || '-'}`} />
                  <Chip label={`Competitors: ${includeCompetitors ? 'Included' : 'Excluded'}`} />
                  <Chip label={`Dates: ${startDate || '-'} to ${endDate || startDate || '-'}`} />
                </Stack>
              </Paper>

              <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                <Button onClick={() => setStep(1)} disabled={loading}>
                  Back
                </Button>
                <Button
                  variant="contained"
                  onClick={handleStartScraping}
                  disabled={loading}
                  startIcon={loading ? <CircularProgress size={18} /> : null}
                >
                  {loading ? 'Starting' : 'Start Scraping'}
                </Button>
              </Box>
            </Stack>
          </Paper>
        )}

        {step === 3 && taskId && (
          <Stack spacing={3}>
            <Paper elevation={2} sx={{ p: 3 }}>
              <Grid container spacing={2} alignItems="center">
                <Grid item xs={6} md={3}>
                  <Typography variant="h5" fontWeight={700}>
                    {taskStatus?.progress || 0}%
                  </Typography>
                  <Typography color="text.secondary">Progress</Typography>
                </Grid>
                <Grid item xs={6} md={3}>
                  <Typography variant="h5" fontWeight={700}>
                    {taskStatus?.records_count || 0}
                  </Typography>
                  <Typography color="text.secondary">Priced Flights</Typography>
                </Grid>
                <Grid item xs={6} md={3}>
                  <Chip
                    color={taskStatus?.status === 'completed' ? 'success' : taskStatus?.status === 'failed' ? 'error' : 'primary'}
                    label={taskStatus?.status || 'running'}
                  />
                </Grid>
                <Grid item xs={6} md={3}>
                  <Typography variant="h5" fontWeight={700}>
                    {taskStatus?.airlines_scraped?.length || 0}
                  </Typography>
                  <Typography color="text.secondary">Airlines</Typography>
                </Grid>
              </Grid>
            </Paper>

            {taskStatus?.status === 'completed' && (
              <>
                {taskStatus?.message && <Alert severity="info">{taskStatus.message}</Alert>}
                {taskStatus?.debug_artifacts?.length > 0 && (
                  <Paper elevation={1} sx={{ p: 2 }}>
                    <Typography variant="h6" gutterBottom>
                      Scraper Debug Evidence
                    </Typography>
                    <Typography color="text.secondary" sx={{ mb: 1 }}>
                      These files show the airline pages that opened during scraping.
                    </Typography>
                    <Stack direction="row" spacing={1} useFlexGap flexWrap="wrap">
                      {taskStatus.debug_artifacts.map((artifact) => (
                        <Button
                          key={artifact.filename}
                          size="small"
                          variant="outlined"
                          href={`http://localhost:8000${artifact.url}`}
                          target="_blank"
                          rel="noreferrer"
                        >
                          {artifact.type}: {artifact.filename.split('_').slice(-2).join('_')}
                        </Button>
                      ))}
                    </Stack>
                  </Paper>
                )}
                <FlightResults
                  taskId={taskId}
                  origin={selectedRoute?.origin}
                  destination={selectedRoute?.destination}
                />
                <Box sx={{ display: 'flex', justifyContent: 'center', gap: 2, flexWrap: 'wrap' }}>
                  {taskStatus?.output_filename && (
                    <Button
                      variant="contained"
                      href={`http://localhost:8000/api/download/${encodeURIComponent(
                        taskStatus.output_filename.replace(/\.xlsx$/i, '')
                      )}`}
                    >
                      Download Excel
                    </Button>
                  )}
                  <Button variant="outlined" href="/fare_intelligence.html">
                    Open Visualization
                  </Button>
                  <Button variant="outlined" onClick={resetForm}>
                    Start New Search
                  </Button>
                </Box>
              </>
            )}

            {taskStatus?.status === 'failed' && (
              <Stack spacing={2}>
                <Alert severity="error">
                  Scraping failed: {taskStatus.error || taskStatus.error_message || 'Unknown error'}
                </Alert>
                {taskStatus?.output_filename && (
                  <Box>
                    <Button
                      variant="contained"
                      href={`http://localhost:8000/api/download/${encodeURIComponent(
                        taskStatus.output_filename.replace(/\.xlsx$/i, '')
                      )}`}
                    >
                      Download Partial Excel
                    </Button>
                  </Box>
                )}
              </Stack>
            )}
          </Stack>
        )}
      </Stack>
    </Container>
  );
};

export default MultiAirlineDashboard;
