import React from 'react';
import { useNavigate } from 'react-router-dom';
import { AppBar, Toolbar, Typography, Box, Container } from '@mui/material';
import { ButtonGroup } from './ButtonGroup/ButtonGroup';
import { ThemeButton } from '@ui';

const Header = () => {
  const navigate = useNavigate();

  return (
    <AppBar
      position="static"
      sx={{
        backgroundColor: '#fff',
        color: 'text.primary',
        boxShadow: 1,
        width: '100%',
        marginLeft: 0,
        marginRight: 0,
        marginTop: 0,
        borderRadius: 0,
      }}
      elevation={0}
    >
      <Container maxWidth="xl" disableGutters>
        <Toolbar
          sx={{
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            width: '100%',
            padding: '0.5rem 1rem',
          }}
        >
          <Box sx={{ display: 'flex', alignItems: 'center' }}>
            <Typography
              variant="h6"
              component="div"
              sx={{
                textAlign: 'left',
                marginRight: '16px',
                color: 'black',
                cursor: 'pointer',
                '&:hover': {
                  opacity: 0.8,
                },
              }}
              onClick={() => navigate('/')}
            >
              My Hotel App
            </Typography>
            <ThemeButton />
          </Box>
          <ButtonGroup />
        </Toolbar>
      </Container>
    </AppBar>
  );
};

export default Header;
