'use client'

import React, { useState } from "react";
import {
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  ListSubheader,
  OutlinedInput,
  SelectChangeEvent,
  Box,
  Chip,
  TextField,
  Typography,
  Button,
  Paper,
  Stack,
  InputAdornment,
  Grid,
} from "@mui/material";
import CancelIcon from "@mui/icons-material/Cancel";
import SendIcon from "@mui/icons-material/Send";

// Data Structure for our Event Groups
const eventGroups = [
  { label: "Freestyle", items: ["50 Free", "100 Free", "200 Free", "500 Free"] },
  { label: "Backstroke", items: ["50 Back", "100 Back", "200 Back"] },
  { label: "Breaststroke", items: ["50 Breast", "100 Breast", "200 Breast"] },
  { label: "Butterfly", items: ["50 Fly", "100 Fly", "200 Fly"] },
  { label: "Medley", items: ["100 IM", "200 IM", "400 IM"] },
];

interface SkillOption {
  label: string;
  value: string;
}

const skillLevels: SkillOption[] = [
  { label: "Recreational", value: "Recreational" },
  { label: "Developmental", value: "Developmental" },
  { label: "Competitive", value: "Competitive" },
  { label: "Elite", value: "Elite" }
];

export default function SwimmerProfileForm() {
  // --- STATE MANAGEMENT ---
  const [selectedEvents, setSelectedEvents] = useState<string[]>([]);
  const [eventTimes, setEventTimes] = useState<{ [key: string]: string }>({});
  
  const [vitals, setVitals] = useState({
    age: "",
    height: "",
  });

  const [skillLevel, setSkillLevel] = useState<string>("");

  const [kpis, setKpis] = useState({
    backsquat: "",
    deadlift: "",
    benchpress: "",
    powerclean: "",
    snatch: "",
    verticalleap: "",
  });

  const [meets, setMeets] = useState([
    { name: "", date: "" }
  ]);

  const [agentNotes, setAgentNotes] = useState("");

  // --- HANDLERS ---
  
  // Handle Event Selection
  const handleEventChange = (event: SelectChangeEvent<typeof selectedEvents>) => {
    const { target: { value } } = event;
    const newSelection = typeof value === "string" ? value.split(",") : value;
    
    setSelectedEvents(newSelection);

    // Cleanup times for events that were unselected
    setEventTimes((prev) => {
      const updatedTimes = { ...prev };
      Object.keys(updatedTimes).forEach((evt) => {
        if (!newSelection.includes(evt)) {
          delete updatedTimes[evt];
        }
      });
      return updatedTimes;
    });
  };

  // Handle Event Deletion from Chips
  const handleDeleteEvent = (eventToDelete: string) => {
    setSelectedEvents((prev) => prev.filter((item) => item !== eventToDelete));
    
    // Cleanup time for the deleted event
    setEventTimes((prev) => {
      const updatedTimes = { ...prev };
      delete updatedTimes[eventToDelete];
      return updatedTimes;
    });
  };

  const handleSkillLevelChange = (event: SelectChangeEvent) => {
    setSkillLevel(event.target.value);
  };

  // Handle Input Changes for generic objects
  const handleVitalChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setVitals({ ...vitals, [e.target.name]: e.target.value });
  };

  const handleKpiChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setKpis({ ...kpis, [e.target.name]: e.target.value });
  };

  // Handler to add a new empty meet row
  const addMeet = () => {
    setMeets([...meets, { name: "", date: "" }]);
  };

  // Handler to update a specific meet
  const handleMeetChange = (index: number, field: "name" | "date", value: string) => {
    const updatedMeets = [...meets];
    updatedMeets[index][field] = value;
    setMeets(updatedMeets);
  };

  // Handler to remove a meet
  const removeMeet = (index: number) => {
    setMeets(meets.filter((_, i) => i !== index));
  };

  const handleTimeChange = (eventName: string, timeValue: string) => {
    setEventTimes({ ...eventTimes, [eventName]: timeValue });
  };

  // Submit Handler
  const handleSubmit = async (e: React.ChangeEvent<HTMLFormElement>) => {
    e.preventDefault();
    
    // Construct the payload for your Python backend
    const payload = {
      vitals,
      skillLevel,
      kpis,
      swimData: {
        events: selectedEvents,
        times: eventTimes,
      },
      meets,
      agentNotes,
    };

    // sends the payload to the backend and logs the response (the generated plan)
    console.log("Submitting payload to backend:", payload);
    const res = await fetch("http://localhost:8000/run", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });

    const plan = await res.json();
    console.log("Plan:", plan);
  };

  return (
    <Box sx={{ p: 4, display: 'flex', justifyContent: 'center', bgcolor: '#ffffff', minHeight: '100vh' }}>
      <Paper elevation={3} sx={{ p: 4, width: '100%', maxWidth: 600 }}>
        <Typography variant="h4" gutterBottom sx={{ fontWeight: "bold" }}>
          Athlete Profile Setup
        </Typography>

        <form onSubmit={handleSubmit}>
          <Stack spacing={2}>
            
            {/* --- SECTION 1: Vitals --- */}
            <Box>
              <Typography variant="h6" gutterBottom color="primary">
                Demographics & Vitals
              </Typography>
              <Stack direction={{ xs: 'column', sm: 'row' }} spacing={2}>
                <TextField label="Age" name="age" type="number" slotProps={{ input: { inputProps: {min: 0}, endAdornment: <InputAdornment position="end"></InputAdornment>}}} value={vitals.age} onChange={handleVitalChange} fullWidth />
                <TextField label="Height" name="height" placeholder="e.g. 6'2&quot;" value={vitals.height} onChange={handleVitalChange} fullWidth />
                <FormControl fullWidth>
                  <InputLabel id="skill-level-label">Skill Level</InputLabel>
                  <Select
                    labelId="skill-level-label"
                    name="skillLevel" // Matches your state key
                    value={skillLevel || ''} 
                    label="Skill Level"
                    onChange={handleSkillLevelChange}
                  >
                    {skillLevels.map((option: SkillOption) => (
                      <MenuItem key={option.value} value={option.value}>
                        {option.label}
                      </MenuItem>
                    ))}
                  </Select>
                </FormControl>
              </Stack>
            </Box>

            {/* --- SECTION 2: KPIs --- */}
            <Box>
              <Typography variant="h6" gutterBottom color="primary">
                Strength KPIs
              </Typography>
              <Grid container spacing={2}>
                <Grid size={{ xs: 12, md: 4, sm: 6 }}>
                  <TextField label="Backsquat" name="backsquat" type="number" slotProps={{ input: { inputProps: {min: 0}, endAdornment: <InputAdornment position="end">lbs</InputAdornment> } }} value={kpis.backsquat} onChange={handleKpiChange} fullWidth />
                </Grid>
                <Grid size={{ xs: 12, md: 4, sm: 6 }}>
                  <TextField label="Deadlift" name="deadlift" type="number" slotProps={{ input: { inputProps: {min: 0}, endAdornment: <InputAdornment position="end">lbs</InputAdornment> } }} value={kpis.deadlift} onChange={handleKpiChange} fullWidth />
                </Grid>
                <Grid size={{ xs: 12, md: 4, sm: 6 }}>
                  <TextField label="Bench Press" name="benchpress" type="number" slotProps={{ input: { inputProps: {min: 0}, endAdornment: <InputAdornment position="end">lbs</InputAdornment> } }} value={kpis.benchpress} onChange={handleKpiChange} fullWidth />
                </Grid>
                <Grid size={{ xs: 12, md: 4, sm: 6 }}>
                  <TextField label="Power Clean" name="powerclean" type="number" slotProps={{ input: { inputProps: {min: 0}, endAdornment: <InputAdornment position="end">lbs</InputAdornment> } }} value={kpis.powerclean} onChange={handleKpiChange} fullWidth />
                </Grid>
                <Grid size={{ xs: 12, md: 4, sm: 6 }}>
                  <TextField label="Snatch" name="snatch" type="number" slotProps={{ input: { inputProps: {min: 0}, endAdornment: <InputAdornment position="end">lbs</InputAdornment> } }} value={kpis.snatch} onChange={handleKpiChange} fullWidth />
                </Grid>
                <Grid size={{ xs: 12, md: 4, sm: 6 }}>
                  <TextField label="Vertical Leap" name="verticalleap" type="number" slotProps={{ input: { inputProps: {min: 0}, endAdornment: <InputAdornment position="end">inches</InputAdornment> } }} value={kpis.verticalleap} onChange={handleKpiChange} fullWidth />
                </Grid>

              </Grid>
            </Box>

            {/* --- SECTION 3: Swim Events & Times --- */}
            <Box>
              <Typography variant="h6" gutterBottom color="primary">
                Swim Events & Current Times
              </Typography>
              
              <FormControl fullWidth sx={{ mb: 2 }}>
                <InputLabel id="events-label">Select Your Events</InputLabel>
                <Select
                  labelId="events-label"
                  multiple
                  value={selectedEvents}
                  onChange={handleEventChange}
                  input={<OutlinedInput label="Select Your Events" />}
                  renderValue={(selected) => (
                    <Box sx={{ display: "flex", flexWrap: "wrap", gap: 0.5 }}>
                      {selected.map((value) => (
                        <Chip
                          key={value}
                          label={value}
                          deleteIcon={
                            <CancelIcon onMouseDown={(e) => e.stopPropagation()} />
                          }
                          onDelete={() => handleDeleteEvent(value)}
                        />
                      ))}
                    </Box>
                  )}
                >
                  {eventGroups.map((group) => [
                    <ListSubheader key={group.label}>{group.label}</ListSubheader>,
                    group.items.map((eventName) => (
                      <MenuItem key={eventName} value={eventName}>
                        {eventName}
                      </MenuItem>
                    )),
                  ])}
                </Select>
              </FormControl>

              {/* Dynamically render text fields for selected events */}
              {selectedEvents.length > 0 && (
                <Stack spacing={2} sx={{ mt: 2, p: 2, bgcolor: '#fafafa', borderRadius: 1, border: '1px solid #e0e0e0' }}>
                  <Typography variant="subtitle2" color="textSecondary">
                    Enter Personal Best Times for Selected Events
                  </Typography>
                  {selectedEvents.map((eventName) => (
                    <TextField
                      key={`time-${eventName}`}
                      label={`${eventName} Time`}
                      placeholder="e.g. 21.50 or 1:45.20"
                      value={eventTimes[eventName] || ""}
                      onChange={(e) => handleTimeChange(eventName, e.target.value)}
                      size="small"
                      fullWidth
                    />
                  ))}
                </Stack>
              )}
            </Box>
            {/* --- SECTION 4: Meet Dates --- */}
            <Box>
              <Typography variant="h6" gutterBottom color="primary">
                Upcoming Meets
              </Typography>
              
              <Stack spacing={2}>
                {meets.map((meet, index) => (
                  <Box 
                    key={index} 
                    sx={{ 
                      display: 'flex', 
                      flexDirection: { xs: 'column', sm: 'row' },
                      gap: 2, 
                      alignItems: { xs: 'stretch', sm: 'center' }
                    }}
                  >
                    <TextField
                      label="Meet Name"
                      placeholder="e.g. Junior Nationals"
                      value={meet.name}
                      onChange={(e) => handleMeetChange(index, "name", e.target.value)}
                      sx={{ flex: 1 }} 
                    />

                    <TextField
                      label="Date"
                      type="date"
                      slotProps={{ inputLabel: { shrink: true } }}
                      value={meet.date}
                      onChange={(e) => handleMeetChange(index, "date", e.target.value)}
                      sx={{ width: { xs: '100%', sm: '200px' } }} 
                    />

                    <Button 
                      variant="outlined"
                      color="error" 
                      onClick={() => removeMeet(index)}
                      disabled={meets.length === 1}
                      sx={{ height: '56px', minWidth: '100px' }} 
                    >
                      Remove
                    </Button>
                  </Box>
                ))}

                {/* The Add Button goes OUTSIDE the map, but INSIDE the Stack */}
                <Button 
                  variant="outlined" 
                  color="primary"
                  onClick={addMeet} 
                  sx={{ alignSelf: 'center', mt: 1 }}
                >
                  + Add Another Meet
                </Button>
              </Stack>
            </Box>

            {/* --- SECTION 5: Agent Input --- */}
            <Box>
              <Typography variant="h6" gutterBottom color="primary">
                Additional Context (AI Agent)
              </Typography>
              <Typography variant="body2" color="textSecondary" sx={{ mb: 1 }}>
                Provide any recent injuries, training goals, or nutritional context.
              </Typography>
              <TextField
                multiline
                rows={4}
                fullWidth
                placeholder="I am currently recovering from a minor shoulder impingement..."
                value={agentNotes}
                onChange={(e) => setAgentNotes(e.target.value)}
              />
            </Box>

            {/* --- SUBMIT --- */}
            <Button
              type="submit"
              variant="contained"
              size="large"
              endIcon={<SendIcon />}
              sx={{ py: 1.5, mt: 2 }}
            >
              Generate Training Plan
            </Button>

          </Stack>
        </form>
      </Paper>
    </Box>
  );
}