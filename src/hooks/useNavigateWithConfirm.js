import { useCallback, useState } from 'react';
import { useNavigate } from 'react-router-dom';

export const useNavigateWithConfirm = () => {
  const navigate = useNavigate();
  const [showDialog, setShowDialog] = useState(false);
  const [pendingPath, setPendingPath] = useState(null);

  const handleNavigate = useCallback(
    (path, shouldConfirm = false) => {
      if (shouldConfirm) {
        setPendingPath(path);
        setShowDialog(true);
      } else {
        navigate(path);
      }
    },
    [navigate]
  );

  const handleConfirm = useCallback(() => {
    if (pendingPath) {
      navigate(pendingPath);
    }
    setShowDialog(false);
  }, [navigate, pendingPath]);

  const handleCancel = useCallback(() => {
    setPendingPath(null);
    setShowDialog(false);
  }, []);

  return {
    showDialog,
    handleNavigate,
    handleConfirm,
    handleCancel,
  };
};
