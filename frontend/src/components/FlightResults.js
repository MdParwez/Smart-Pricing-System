import React, { useEffect, useMemo, useState } from 'react';
import {
  Alert,
  Box,
  Chip,
  CircularProgress,
  FormControl,
  Grid,
  InputLabel,
  MenuItem,
  Paper,
  Select,
  Stack,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Typography,
} from '@mui/material';
import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts';
import { scraperService } from '../services/scraperService';

const COLORS = ['#1976d2', '#d32f2f', '#2e7d32', '#ed6c02', '#7b1fa2'];

const formatPrice = (value, currency = 'EUR') => {
  if (typeof value !== 'number' || Number.isNaN(value)) return value || 'N/A';
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency,
    maximumFractionDigits: 2,
  }).format(value);
};

const FlightResults = ({ taskId, origin, destination }) => {
  const [flights, setFlights] = useState([]);
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [sortBy, setSortBy] = useState('price');

  useEffect(() => {
    const fetchData = async () => {
      if (!taskId || !origin || !destination) return;

      try {
        setLoading(true);
        setError('');
        const flightData = await scraperService.getTaskFlights(taskId);
        setFlights(flightData.flights || []);
      } catch (err) {
        setError(`Failed to load flight results: ${err.message}`);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [taskId, origin, destination]);

  useEffect(() => {
    const prices = flights
      .map((flight) => flight.price)
      .filter((price) => typeof price === 'number' && !Number.isNaN(price));

    if (!prices.length) {
      setStats(null);
      return;
    }

    const airlines = [...new Set(flights.map((flight) => flight.airline).filter(Boolean))];
    const byAirline = {};
    airlines.forEach((airline) => {
      const airlineFlights = flights.filter((flight) => flight.airline === airline);
      const airlinePrices = airlineFlights
        .map((flight) => flight.price)
        .filter((price) => typeof price === 'number' && !Number.isNaN(price));
      if (!airlinePrices.length) return;
      byAirline[airline] = {
        count: airlineFlights.length,
        min_price: Math.min(...airlinePrices),
        avg_price: airlinePrices.reduce((sum, price) => sum + price, 0) / airlinePrices.length,
      };
    });

    setStats({
      total_flights: flights.length,
      airlines_count: airlines.length,
      airlines,
      price_stats: {
        minimum: Math.min(...prices),
        maximum: Math.max(...prices),
        average: prices.reduce((sum, price) => sum + price, 0) / prices.length,
        median: [...prices].sort((a, b) => a - b)[Math.floor(prices.length / 2)],
      },
      by_airline: byAirline,
    });
  }, [flights]);

  const sortedFlights = useMemo(() => {
    return [...flights].sort((a, b) => {
      if (sortBy === 'price') {
        const aPrice = typeof a.price === 'number' ? a.price : Number.MAX_SAFE_INTEGER;
        const bPrice = typeof b.price === 'number' ? b.price : Number.MAX_SAFE_INTEGER;
        return aPrice - bPrice;
      }
      if (sortBy === 'airline') {
        return String(a.airline || '').localeCompare(String(b.airline || ''));
      }
      if (sortBy === 'departure') {
        return String(a.departure_time || '').localeCompare(String(b.departure_time || ''));
      }
      return 0;
    });
  }, [flights, sortBy]);

  const airlineChartData = stats?.by_airline
    ? Object.entries(stats.by_airline).map(([airline, data]) => ({
        name: airline,
        price: data.avg_price,
        count: data.count,
      }))
    : [];

  if (loading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', py: 4 }}>
        <CircularProgress />
      </Box>
    );
  }

  return (
    <Stack spacing={3}>
      {error && <Alert severity="error">{error}</Alert>}

      {stats && (
        <Grid container spacing={2}>
          <Grid item xs={12} sm={6} md={3}>
            <Paper elevation={1} sx={{ p: 2 }}>
              <Typography variant="h5" fontWeight={700}>{stats.total_flights}</Typography>
              <Typography color="text.secondary">Total Flights</Typography>
            </Paper>
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <Paper elevation={1} sx={{ p: 2 }}>
              <Typography variant="h5" fontWeight={700}>
                {formatPrice(stats.price_stats?.minimum)}
              </Typography>
              <Typography color="text.secondary">Lowest Price</Typography>
            </Paper>
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <Paper elevation={1} sx={{ p: 2 }}>
              <Typography variant="h5" fontWeight={700}>
                {formatPrice(stats.price_stats?.average)}
              </Typography>
              <Typography color="text.secondary">Average Price</Typography>
            </Paper>
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <Paper elevation={1} sx={{ p: 2 }}>
              <Typography variant="h5" fontWeight={700}>{stats.airlines_count}</Typography>
              <Typography color="text.secondary">Airlines</Typography>
            </Paper>
          </Grid>
        </Grid>
      )}

      {airlineChartData.length > 0 && (
        <Grid container spacing={2}>
          <Grid item xs={12} lg={6}>
            <Paper elevation={1} sx={{ p: 2 }}>
              <Typography variant="h6" gutterBottom>Average Price by Airline</Typography>
              <ResponsiveContainer width="100%" height={280}>
                <BarChart data={airlineChartData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="name" />
                  <YAxis />
                  <Tooltip formatter={(value) => formatPrice(value)} />
                  <Bar dataKey="price" fill="#1976d2" />
                </BarChart>
              </ResponsiveContainer>
            </Paper>
          </Grid>
          <Grid item xs={12} lg={6}>
            <Paper elevation={1} sx={{ p: 2 }}>
              <Typography variant="h6" gutterBottom>Flight Count by Airline</Typography>
              <ResponsiveContainer width="100%" height={280}>
                <PieChart>
                  <Pie
                    data={airlineChartData}
                    cx="50%"
                    cy="50%"
                    label={({ name, count }) => `${name}: ${count}`}
                    outerRadius={90}
                    dataKey="count"
                  >
                    {airlineChartData.map((_, index) => (
                      <Cell key={index} fill={COLORS[index % COLORS.length]} />
                    ))}
                  </Pie>
                  <Tooltip />
                </PieChart>
              </ResponsiveContainer>
            </Paper>
          </Grid>
        </Grid>
      )}

      <Paper elevation={1} sx={{ p: 2 }}>
        <Stack direction={{ xs: 'column', sm: 'row' }} justifyContent="space-between" spacing={2} sx={{ mb: 2 }}>
          <Typography variant="h6">Flights</Typography>
          <FormControl size="small" sx={{ minWidth: 180 }}>
            <InputLabel>Sort By</InputLabel>
            <Select value={sortBy} label="Sort By" onChange={(event) => setSortBy(event.target.value)}>
              <MenuItem value="price">Price</MenuItem>
              <MenuItem value="airline">Airline</MenuItem>
              <MenuItem value="departure">Departure</MenuItem>
            </Select>
          </FormControl>
        </Stack>

        {sortedFlights.length === 0 ? (
          <Typography color="text.secondary" align="center" sx={{ py: 4 }}>
            No flights found.
          </Typography>
        ) : (
          <TableContainer>
            <Table size="small">
              <TableHead>
                <TableRow>
                  <TableCell>Airline</TableCell>
                  <TableCell>Date</TableCell>
                  <TableCell>Flight</TableCell>
                  <TableCell>Departure</TableCell>
                  <TableCell>Arrival</TableCell>
                  <TableCell>Duration</TableCell>
                  <TableCell>Stops</TableCell>
                  <TableCell align="right">Price</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {sortedFlights.slice(0, 50).map((flight, index) => (
                  <TableRow key={`${flight.airline}-${flight.date}-${flight.departure_time}-${index}`}>
                    <TableCell><Chip label={flight.airline} size="small" /></TableCell>
                    <TableCell>{flight.date}</TableCell>
                    <TableCell>{flight.flight_number || '-'}</TableCell>
                    <TableCell>{flight.departure_time}</TableCell>
                    <TableCell>{flight.arrival_time}</TableCell>
                    <TableCell>{flight.duration}</TableCell>
                    <TableCell>{flight.stops || 'Unknown'}</TableCell>
                    <TableCell align="right">
                      <strong>{formatPrice(flight.price, flight.currency || 'EUR')}</strong>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>
        )}
      </Paper>
    </Stack>
  );
};

export default FlightResults;
