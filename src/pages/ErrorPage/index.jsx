import { Box, Typography, Button } from '@mui/material';
import { Footer, Header, PageLayout } from '@components';
import { useNavigate } from 'react-router-dom';

export function ErrorPage() {
  const navigate = useNavigate();

  return (
    <PageLayout
      renderHeader={() => <Header />}
      renderContent={() => (
        <Box
          sx={{
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            gap: 3,
            marginY: 8,
          }}
        >
          <Typography variant="h1" color="primary" sx={{ fontWeight: 800 }}>
            Oops!
          </Typography>
          <Typography variant="h6">
            Sorry, an unexpected error has occurred.
          </Typography>
          <Button variant="contained" onClick={() => navigate('/')}>
            Return to Home
          </Button>
        </Box>
      )}
      renderFooter={() => <Footer />}
    />
  );
}
