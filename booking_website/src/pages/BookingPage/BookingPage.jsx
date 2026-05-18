import { useState, useEffect, useMemo } from 'react';
import {
  useParams,
  useNavigate,
  Navigate,
  useLocation,
} from 'react-router-dom';
import { useSelector, useDispatch } from 'react-redux';
import {
  Container,
  Typography,
  Button,
  Box,
  Alert,
  Paper,
  TextField,
  Divider,
  CircularProgress,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
} from '@mui/material';
import { DatePicker } from '@mui/x-date-pickers/DatePicker';
import { AdapterDateFns } from '@mui/x-date-pickers/AdapterDateFns';
import { LocalizationProvider } from '@mui/x-date-pickers/LocalizationProvider';
import { PageLayout, Header, Footer } from '@components';
import { CREATE_BOOKING_ACTION } from '@store/bookings/bookings.actions';
import { FETCH_HOTELS_ACTION } from '@store/hotels/hotels.actions';
import { createDialogPortal } from '@utils/portal';

export const BookingPage = () => {
  const { hotelId } = useParams();
  const location = useLocation();
  const initialBooking = location.state?.initialBooking;

  const [checkIn, setCheckIn] = useState(
    initialBooking ? new Date(initialBooking.checkIn) : null
  );
  const [checkOut, setCheckOut] = useState(
    initialBooking ? new Date(initialBooking.checkOut) : null
  );
  const [guestCount, setGuestCount] = useState(initialBooking?.guestCount || 1);

  const navigate = useNavigate();
  const dispatch = useDispatch();
  const hotel = useSelector((state) =>
    state.hotels.hotels.find((h) => h.id === hotelId)
  );
  const currentUser = useSelector((state) => state.users.currentUser);
  const [error, setError] = useState(null);
  const [showExitDialog, setShowExitDialog] = useState(false);
  const [intendedPath, setIntendedPath] = useState(null);
  const [portalData, setPortalData] = useState(null);

  useEffect(() => {
    dispatch(FETCH_HOTELS_ACTION());
  }, [dispatch]);

  useEffect(() => {
    return () => {
      if (portalData?.cleanup) {
        portalData.cleanup();
      }
    };
  }, [portalData]);

  const dialogContent = useMemo(() => {
    if (!showExitDialog) return null;

    return (
      <Dialog
        open={true}
        onClose={() => setShowExitDialog(false)}
        aria-labelledby="exit-dialog-title"
        aria-describedby="exit-dialog-description"
      >
        <DialogTitle id="exit-dialog-title">Cancel Booking</DialogTitle>
        <DialogContent id="exit-dialog-description">
          Are you sure you want to leave? Your booking information will be lost.
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setShowExitDialog(false)} autoFocus>
            No, Stay
          </Button>
          <Button
            onClick={() => {
              setShowExitDialog(false);
              navigate(intendedPath);
            }}
            color="error"
          >
            Yes, Leave
          </Button>
        </DialogActions>
      </Dialog>
    );
  }, [showExitDialog, intendedPath, navigate]);

  useEffect(() => {
    if (dialogContent) {
      const newPortalData = createDialogPortal(dialogContent);
      setPortalData(newPortalData);
      return () => newPortalData.cleanup();
    }
    return undefined;
  }, [dialogContent]);

  if (!hotel) {
    return (
      <Container sx={{ mt: 4 }}>
        <CircularProgress />
      </Container>
    );
  }

  if (!currentUser) {
    return (
      <Navigate to="/login" state={{ from: `/booking/${hotelId}` }} replace />
    );
  }

  const handleBooking = () => {
    if (!checkIn || !checkOut) {
      setError('Please select both check-in and check-out dates');
      return;
    }

    if (checkIn >= checkOut) {
      setError('Check-out date must be after check-in date');
      return;
    }

    dispatch({
      type: CREATE_BOOKING_ACTION,
      payload: {
        hotelId,
        userId: currentUser.id,
        userName: currentUser.name,
        checkIn: checkIn.toISOString(),
        checkOut: checkOut.toISOString(),
        guestCount,
        status: 'confirmed',
        createdAt: new Date().toISOString(),
      },
    });

    navigate('/profile');
  };

  return (
    <PageLayout
      renderHeader={() => <Header />}
      renderContent={() => (
        <>
          <Container maxWidth="md" sx={{ my: 4 }}>
            <Paper sx={{ p: 3 }}>
              <Typography variant="h4" gutterBottom>
                Book Your Stay at {hotel.name}
              </Typography>
              <Typography variant="body1" color="text.secondary" gutterBottom>
                {hotel.city}
              </Typography>

              <Divider sx={{ my: 3 }} />

              <Box sx={{ my: 4, display: 'flex', gap: 2 }}>
                <LocalizationProvider dateAdapter={AdapterDateFns}>
                  <DatePicker
                    label="Check-in"
                    value={checkIn}
                    onChange={setCheckIn}
                    minDate={new Date()}
                    sx={{ flex: 1 }}
                  />
                  <DatePicker
                    label="Check-out"
                    value={checkOut}
                    onChange={setCheckOut}
                    minDate={checkIn || new Date()}
                    sx={{ flex: 1 }}
                  />
                </LocalizationProvider>
              </Box>

              <TextField
                type="number"
                label="Number of Guests"
                value={guestCount}
                onChange={(e) =>
                  setGuestCount(Math.max(1, parseInt(e.target.value)))
                }
                inputProps={{ min: 1 }}
                fullWidth
                sx={{ mb: 3 }}
              />

              {error && (
                <Alert severity="error" sx={{ mb: 2 }}>
                  {error}
                </Alert>
              )}

              <Button
                variant="contained"
                color="primary"
                fullWidth
                onClick={handleBooking}
                size="large"
              >
                Confirm Booking
              </Button>
            </Paper>
          </Container>
          {portalData?.portal}
        </>
      )}
      renderFooter={() => <Footer />}
    />
  );
};
