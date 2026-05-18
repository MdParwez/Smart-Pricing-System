import React, { useState } from 'react';
import {
  Container,
  Paper,
  Stepper,
  Step,
  StepLabel,
  Button,
  Box,
  Snackbar,
  Alert,
  CircularProgress,
} from '@mui/material';
import ReportInformation from '../components/ReportInformation';
import JourneyInformation from '../components/JourneyInformation';
import DateSelection from '../components/DateSelection';
import ChannelSelection from '../components/ChannelSelection';
import ScheduleDialog from '../components/ScheduleDialog';
import { scraperService } from '../services/scraperService';

const steps = ['Report Information', 'Journey Information', 'Dates', 'Channel'];

const initialFormData = {
  reportName: '',
  reportDescription: '',
  userNotes: '',
  reportType: 'standard',
  journeyType: 'one-way',
  passengerType: { adult: 1, child: 0, infant: 0 },
  classOfService: 'economy',
  stops: 'non-stop',
  origin: '',
  destination: '',
  airline: 'all',
  reverseOND: false,
  dateRange: 'continuous',
  outboundDateFrom: null,
  outboundDateTo: null,
  inboundDateFrom: null,
  inboundDateTo: null,
  daysOfWeek: [],
  departureTime: 'any',
  considerFarthestDate: false,
  channel: 'playwright',
};

export default function Dashboard() {
  const [activeStep, setActiveStep] = useState(0);
  const [formData, setFormData] = useState(initialFormData);
  const [openScheduleDialog, setOpenScheduleDialog] = useState(false);
  const [loading, setLoading] = useState(false);
  const [snackbar, setSnackbar] = useState({
    open: false,
    message: '',
    severity: 'success',
  });

  const resetForm = () => {
    setFormData(initialFormData);
    setActiveStep(0);
  };

  const handleNext = () => {
    if (activeStep === steps.length - 1) {
      setOpenScheduleDialog(true);
    } else {
      setActiveStep((prevStep) => prevStep + 1);
    }
  };

  const handleBack = () => {
    setActiveStep((prevStep) => prevStep - 1);
  };

  const handleFormChange = (updates) => {
    setFormData((prev) => ({ ...prev, ...updates }));
  };

  const waitForScrapeCompletion = async (taskId) => {
    if (!taskId) return null;

    const maxAttempts = 360;
    for (let attempt = 0; attempt < maxAttempts; attempt += 1) {
      await new Promise((resolve) => setTimeout(resolve, 5000));
      const status = await scraperService.getScrapingStatus(taskId);

      if (status.status === 'completed') {
        return status;
      }

      if (status.status === 'error') {
        throw new Error(status.error || 'Scraping failed');
      }
    }

    throw new Error('Scraping is still running. Please open the visualization after it completes.');
  };

  const handleScrapeNow = async () => {
    try {
      setLoading(true);
      const response = await scraperService.startScrape(formData);
      setSnackbar({
        open: true,
        message: 'Scraping started. The visualization will open when real data is ready.',
        severity: 'success',
      });
      await waitForScrapeCompletion(response.task_id);
      resetForm();
      setOpenScheduleDialog(false);
      window.location.href = '/fare_intelligence.html';
    } catch (error) {
      setSnackbar({
        open: true,
        message: `Error: ${error.message}`,
        severity: 'error',
      });
    } finally {
      setLoading(false);
    }
  };

  const handleScheduleScrape = async (scheduleData) => {
    try {
      setLoading(true);
      const payload = {
        ...formData,
        ...scheduleData,
      };
      await scraperService.scheduleScrape(payload);
      setSnackbar({
        open: true,
        message: 'Scraping scheduled successfully!',
        severity: 'success',
      });
      setOpenScheduleDialog(false);
      resetForm();
    } catch (error) {
      setSnackbar({
        open: true,
        message: `Error: ${error.message}`,
        severity: 'error',
      });
    } finally {
      setLoading(false);
    }
  };

  const renderStepContent = (step) => {
    switch (step) {
      case 0:
        return <ReportInformation formData={formData} onChange={handleFormChange} />;
      case 1:
        return <JourneyInformation formData={formData} onChange={handleFormChange} />;
      case 2:
        return <DateSelection formData={formData} onChange={handleFormChange} />;
      case 3:
        return <ChannelSelection formData={formData} onChange={handleFormChange} />;
      default:
        return null;
    }
  };

  return (
    <Container maxWidth="lg" sx={{ py: 4 }}>
      <Paper elevation={3} sx={{ p: 4 }}>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', gap: 2, alignItems: 'center', mb: 4 }}>
          <h1 style={{ margin: 0, color: '#333' }}>Flight Fare Intelligence Dashboard</h1>
          <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap', justifyContent: 'flex-end' }}>
            <Button variant="outlined" href="/multi-airline">
              Multi-Airline Scraper
            </Button>
            <Button variant="outlined" href="/fare_intelligence.html">
              Open Visualization
            </Button>
          </Box>
        </Box>

        <Stepper activeStep={activeStep} sx={{ mb: 4 }}>
          {steps.map((label) => (
            <Step key={label}>
              <StepLabel>{label}</StepLabel>
            </Step>
          ))}
        </Stepper>

        <Box sx={{ mb: 4 }}>{renderStepContent(activeStep)}</Box>

        <Box sx={{ display: 'flex', justifyContent: 'space-between', mt: 4 }}>
          <Button disabled={activeStep === 0 || loading} onClick={handleBack}>
            Back
          </Button>
          <Button
            variant="contained"
            color="success"
            onClick={handleNext}
            disabled={loading}
            startIcon={loading ? <CircularProgress size={20} /> : null}
          >
            {activeStep === steps.length - 1 ? 'Save' : 'Next'}
          </Button>
        </Box>
      </Paper>

      <ScheduleDialog
        open={openScheduleDialog}
        onClose={() => setOpenScheduleDialog(false)}
        onScrapeNow={handleScrapeNow}
        onSchedule={handleScheduleScrape}
        loading={loading}
      />

      <Snackbar
        open={snackbar.open}
        autoHideDuration={6000}
        onClose={() => setSnackbar({ ...snackbar, open: false })}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'right' }}
      >
        <Alert severity={snackbar.severity}>{snackbar.message}</Alert>
      </Snackbar>
    </Container>
  );
}
