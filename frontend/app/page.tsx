'use client'

import { useState } from 'react';
import TextField from "@mui/material/TextField";
import MenuItem from "@mui/material/MenuItem";
import ListSubheader from "@mui/material/ListSubheader";

export default function Page() {

  const [events, setEvents] = useState([]);

  const handleChange = (event) => {
    setEvents(event.target.value);
  };

  return (
    <TextField
      select
      sx={{ width: 300 }}
      value={events}
      onChange={handleChange}
      label="Event Selection"
      SelectProps={{
        multiple: true,
        renderValue: (selected) => selected.join(", "),
      }}
    >
      <ListSubheader>Freestyle</ListSubheader>
      <MenuItem value="50 Free">50 Free</MenuItem>
      <MenuItem value="100 Free">100 Free</MenuItem>
      <MenuItem value="200 Free">200 Free</MenuItem>
      <MenuItem value="500 Free">500 Free</MenuItem>
      
      <ListSubheader>Butterfly</ListSubheader>
      <MenuItem value="50 Fly">50 Fly</MenuItem>
      <MenuItem value="100 Fly">100 Fly</MenuItem>
      <MenuItem value="200 Fly">200 Fly</MenuItem>

      <ListSubheader>Backstroke</ListSubheader>
      <MenuItem value="50 Back">50 Back</MenuItem>
      <MenuItem value="100 Back">100 Back</MenuItem>
      <MenuItem value="200 Back">200 Back</MenuItem>

      <ListSubheader>Breaststroke</ListSubheader>
      <MenuItem value="50 Breast">50 Breast</MenuItem>
      <MenuItem value="100 Breast">100 Breast</MenuItem>
      <MenuItem value="200 Breast">200 Breast</MenuItem>
      
      <ListSubheader>Individual Medley</ListSubheader>
      <MenuItem value="100 IM">100 IM</MenuItem>
      <MenuItem value="200 IM">200 IM</MenuItem>
      <MenuItem value="400 IM">400 IM</MenuItem>

    </TextField>
  );
}