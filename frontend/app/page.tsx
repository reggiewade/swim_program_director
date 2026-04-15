'use client'

import { ListSubheader, MenuItem, TextField } from '@mui/material';

export default function Page() {

  return (
    <TextField
      select
      fullWidth
      label="Primary Event"
    >
      <ListSubheader>Freestyle</ListSubheader>
      <MenuItem value="50 Free">50 Free</MenuItem>
      <MenuItem value="100 Free">100 Free</MenuItem>
      
      <ListSubheader>Butterfly</ListSubheader>
      <MenuItem value="50 Fly">50 Fly</MenuItem>
      <MenuItem value="100 Fly">100 Fly</MenuItem>
    </TextField>
  );
}