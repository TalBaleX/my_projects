import React, { useEffect, useState, useCallback, memo } from 'react';
import { useSelector, useDispatch } from 'react-redux';
import { Navigate, useNavigate } from 'react-router-dom';
import {
  Container,
  Typography,
  List,
  ListItem,
  ListItemText,
  Paper,
  Box,
  CircularProgress,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  ButtonGroup,
} from '@mui/material';
import { PageLayout, Header, Footer } from '@components';
import {
  FETCH_USER_BOOKINGS_ACTION,
  DELETE_BOOKING_ACTION,
} from '@store/bookings/bookings.actions';
import { FETCH_HOTELS_ACTION } from '@store/hotels/hotels.actions';
import { format } from 'date-fns';

export const ProfilePage = memo(() => {
  const dispatch = useDispatch();
  const navigate = useNavigate();
  const currentUser = useSelector((state) => state.users?.currentUser);
  const userBookings =
    useSelector((state) => state.bookings?.userBookings) || [];
  const hotels = useSelector((state) => state.hotels.hotels);
  const loading = useSelector((state) => state.bookings?.loading);

  const [openDialog, setOpenDialog] = useState(false);
  const [selectedBooking, setSelectedBooking] = useState(null);

  const [showCancelDialog, setShowCancelDialog] = useState(false);
  const [bookingToCancel, setBookingToCancel] = useState(null);

  useEffect(() => {
    dispatch(FETCH_HOTELS_ACTION());
    if (currentUser?.id) {
      dispatch({ type: FETCH_USER_BOOKINGS_ACTION, payload: currentUser.id });
    }
  }, [dispatch, currentUser]);

  if (!currentUser) {
    return <Navigate to="/login" replace />;
  }

  const handleEdit = useCallback((booking) => {
    setSelectedBooking(booking);
    setOpenDialog(true);
  }, []);

  const handleDelete = useCallback(
    (bookingId) => {
      dispatch({ type: DELETE_BOOKING_ACTION, payload: bookingId });
    },
    [dispatch]
  );

  const handleEditConfirm = useCallback(() => {
    if (selectedBooking) {
      handleDelete(selectedBooking.id);
      setOpenDialog(false);
      navigate(`/booking/${selectedBooking.hotelId}`, {
        state: {
          initialBooking: {
            checkIn: selectedBooking.checkIn,
            checkOut: selectedBooking.checkOut,
            guestCount: selectedBooking.guestCount,
          },
        },
      });
    }
  }, [selectedBooking, handleDelete, navigate]);

  const handleCloseDialog = useCallback(() => {
    setOpenDialog(false);
    setSelectedBooking(null);
  }, []);

  const handleCancelClick = useCallback((booking) => {
    setBookingToCancel(booking);
    setShowCancelDialog(true);
  }, []);

  const handleCancelConfirm = useCallback(() => {
    if (bookingToCancel) {
      handleDelete(bookingToCancel.id);
      setShowCancelDialog(false);
      setBookingToCancel(null);
    }
  }, [bookingToCancel, handleDelete]);

  const handleCancelDialogClose = useCallback(() => {
    setShowCancelDialog(false);
    setBookingToCancel(null);
  }, []);

  const renderContent = useCallback(
    () => (
      <>
        <Container maxWidth="md">
          <Typography variant="h4" align="center" gutterBottom>
            Profile
          </Typography>
          <Typography variant="h6" gutterBottom>
            Welcome, {currentUser.name}
          </Typography>
          <Typography variant="h5" gutterBottom sx={{ mt: 4 }}>
            My Bookings
          </Typography>
          <List>
            {loading ? (
              <Box display="flex" justifyContent="center" p={3}>
                <CircularProgress />
              </Box>
            ) : userBookings.length > 0 ? (
              userBookings.map((booking) => {
                const hotel = hotels.find((h) => h.id === booking.hotelId);
                return (
                  <Paper key={booking.id} sx={{ mb: 2, p: 2 }}>
                    <ListItem
                      secondaryAction={
                        <ButtonGroup>
                          <Button
                            onClick={() => handleEdit(booking)}
                            color="primary"
                          >
                            Edit
                          </Button>
                          <Button
                            onClick={() => handleCancelClick(booking)}
                            color="error"
                          >
                            Cancel
                          </Button>
                        </ButtonGroup>
                      }
                    >
                      <ListItemText
                        primary={hotel?.name || 'Unknown Hotel'}
                        secondary={
                          <>
                            <Typography component="span" display="block">
                              Check-in:{' '}
                              {format(new Date(booking.checkIn), 'PP')}
                            </Typography>
                            <Typography component="span" display="block">
                              Check-out:{' '}
                              {format(new Date(booking.checkOut), 'PP')}
                            </Typography>
                            <Typography component="span" display="block">
                              Guests: {booking.guestCount}
                            </Typography>
                            <Typography component="span" display="block">
                              Status: {booking.status}
                            </Typography>
                          </>
                        }
                      />
                    </ListItem>
                  </Paper>
                );
              })
            ) : (
              <Typography variant="body1" color="text.secondary">
                No bookings yet
              </Typography>
            )}
          </List>
        </Container>

        {selectedBooking && (
          <Dialog open={openDialog} onClose={handleCloseDialog}>
            <DialogTitle>Edit Booking</DialogTitle>
            <DialogContent>
              <Typography>
                Are you sure you want to edit your booking at{' '}
                {hotels.find((h) => h.id === selectedBooking.hotelId)?.name ||
                  'this hotel'}
                ? This will cancel your current booking and create a new one.
              </Typography>
            </DialogContent>
            <DialogActions>
              <Button onClick={handleCloseDialog}>
                No, Keep Current Booking
              </Button>
              <Button
                onClick={handleEditConfirm}
                variant="contained"
                color="primary"
              >
                Yes, Edit Booking
              </Button>
            </DialogActions>
          </Dialog>
        )}

        {bookingToCancel && (
          <Dialog open={showCancelDialog} onClose={handleCancelDialogClose}>
            <DialogTitle>Cancel Booking</DialogTitle>
            <DialogContent>
              <Typography>
                s Are you sure you want to cancel your booking at{' '}
                {hotels.find((h) => h.id === bookingToCancel.hotelId)?.name ||
                  'this hotel'}
                ? This action cannot be undone.
              </Typography>
            </DialogContent>
            <DialogActions>
              <Button onClick={handleCancelDialogClose}>No, Cancel</Button>
              <Button
                onClick={handleCancelConfirm}
                variant="contained"
                color="error"
              >
                Yes, Delete Booking
              </Button>
            </DialogActions>
          </Dialog>
        )}
      </>
    ),
    [
      currentUser,
      loading,
      userBookings,
      hotels,
      selectedBooking,
      openDialog,
      bookingToCancel,
      showCancelDialog,
      handleEdit,
      handleCancelClick,
      handleEditConfirm,
      handleCloseDialog,
      handleCancelDialogClose,
      handleCancelConfirm,
    ]
  );

  const renderHeader = useCallback(() => <Header />, []);
  const renderFooter = useCallback(() => <Footer />, []);

  return (
    <PageLayout
      renderHeader={renderHeader}
      renderContent={renderContent}
      renderFooter={renderFooter}
    />
  );
});
