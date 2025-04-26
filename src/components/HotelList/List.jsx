import { Grid, CircularProgress, Alert, Container, Box } from '@mui/material';
import { Card } from './Card.jsx';
import { useSelector } from 'react-redux';
import { selectHotels, selectHotelsStatus } from '@store';
import { useMemo } from 'react';

export function List() {
  const hotels = useSelector(selectHotels);
  const status = useSelector(selectHotelsStatus);
  const memoizedHotels = useMemo(() => hotels || [], [hotels]);

  if (status === 'loading') {
    return (
      <Box display="flex" justifyContent="center" mt={4}>
        <CircularProgress />
      </Box>
    );
  }

  if (!memoizedHotels.length) {
    return (
      <Box display="flex" justifyContent="center" mt={4}>
        <Alert severity="info">No hotels found</Alert>
      </Box>
    );
  }

  return (
    <Box mt={4}>
      <Container maxWidth="lg">
        <Grid container spacing={2} justifyContent="center">
          {memoizedHotels.map((hotel) => (
            <Grid item xs={12} sm={6} md={4} key={hotel.id}>
              <Card hotel={hotel} />
            </Grid>
          ))}
        </Grid>
      </Container>
    </Box>
  );
}
