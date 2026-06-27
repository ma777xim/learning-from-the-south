# type: ignore
# import Grasshopper as gh

def loadingBar(numerator, denominator):
    percentage = int((numerator / denominator) * 100)
    barLength = int(percentage / 2)
    bar = "█" * barLength + "_" * (50 - barLength)
    print(f"{bar} / {percentage}%")
    if percentage == 0:
        return("initialising...")
    if percentage > 0 and percentage <= 2:
            return("init successful, let's see how it goes")
    if percentage >= 3 and percentage <= 10:
        return("looks well until now :D")
    if percentage >= 11 and percentage <= 49:
        return("did you drink enough water?")    
    if percentage >= 50 and percentage <= 75:
        return("promising, more than halfway through...") 
    if percentage >= 80 and percentage <= 94:
        return("omg, its getting there...") 
    if percentage >= 95 and percentage <= 98:
        return("wow, finishing...") 
    if percentage == 99:
        return("please don't die...")  
    if percentage == 100:
        return("yay! :)")  
    
def br(lineLength, arrayLength):
    char = '_'
    for hi in range(arrayLength):
        print(f"\n{char * lineLength * 10}\n\n")

# sol data

#gh input
#------------------------------------
class MockBranch:
    def __init__(self, data):
        self._data = data
        self.Count = len(data)
    def __getitem__(self, h):
        return self._data[h]

class MockDataTree:
    def __init__(self, data):
        self._branches = data
        self.BranchCount = len(data)
    def Branch(self, i):
        return MockBranch(self._branches[i])
    
#-------------------------------------

num_cells = 100
num_hours = 8

# 2. generate raw dummy data using those constants
raw = [
    [100 + cell * 2 + hour * 10 for hour in range(num_hours)]
    for cell in range(num_cells)
]

# 3. wrap in mock tree
radiation_tree = MockDataTree(raw)

# 4. build solar_matrix from tree (identical to real Ladybug path)
solar_matrix = [
    [radiation_tree.Branch(i)[h] for h in range(radiation_tree.Branch(i).Count)]
    for i in range(radiation_tree.BranchCount)
]

# 5. derive everything else FROM the matrix — single source of truth
num_cells = len(solar_matrix)          # redundant here but good habit for real data
num_hours = len(solar_matrix[0])
grid_size = int(num_cells ** 0.5)
assert grid_size ** 2 == num_cells, f"solar_matrix not square: {num_cells} cells"

# 6. mat props and sim params
T_air = float(20.0)
T_init = T_air  # ← this line is missing
print(f"initial temperature T_init: {T_init} °C")
# etc.

thickness = float(0.2)
print(f"\nslab thickness: {int(thickness * 1000)}mm")
density = float(2300)
print(f"mat density: {density}")
heatCapacity = float(880)
print(f"mat heat capacity: {heatCapacity}")
absorptionCoefficient = float(0.8)
print(f"mat absorption coefficient: {absorptionCoefficient}")
thermalConductivity = float(1.5)
print(f"mat thermal conductivity: {thermalConductivity}")
T_ground = float(10)
print(f"\nground temp T_ground: {T_ground}")
outputHourOfDay = int(14)

if outputHourOfDay + 1 < 12:
    print(f"output hour of day: {outputHourOfDay}am (hour no. {outputHourOfDay})")
else:
    print(f"output hour of day: {outputHourOfDay -12}pm (hour no. {outputHourOfDay})")
A_total = float(1.5)
print(f"slab area A_total: {A_total}")

br(7, 1)

# geoprops per cell
dx = A_total / num_cells
print(f"\nCell width (dx): {dx}")
dy = A_total / num_cells
print(f"Cell height (dy): {dy}")
A_cell = dx * dy
print(f"Cell area (A_cell): {A_cell}")
V_cell = A_cell * thickness
print(f"Cell volume (V_cell): {V_cell}")
m_cell = density * V_cell
print(f"Cell mass (m_cell): {m_cell}")
C_cell = m_cell * heatCapacity
print(f"Cell specific heat capacity (C_cell): {C_cell}")

br(7,1)

# 3. Time stepping config for mathematical stability)
sub_steps = 60 
dt = 3600.0 / sub_steps # 60s intervals
print(f"// Substeps per hour: 3600 / {sub_steps} = {int(dt)}.")

br(7,1)

# Initialize the 2D grid temperature array for the current state
# Mapping 1D flat list index to 2D grid coordinates
T_grid = [[T_init for _ in range(grid_size)] for _ in range(grid_size)]
print(f"list lengths:")
for index, temps in enumerate(T_grid):
    print(f"{index}: {len(temps)}")
if len(set(temps)) == 1:
    print("// Lists O.K.")
    print("// All list lengths are identical ^^")
else:
    print("NOTE: List lengths are not identical")
    
br(7, 1)

# This master list will store the 100 cell temps for EVERY hour
# resultsArchive[hour][cell_flat_index]
resultsArchive = []
print(f"results archive:\n{resultsArchive}\n")
if len(resultsArchive) == 0:
    print('// Archive is empty af.')
else:
    print(f'// Archive has {len(resultsArchive)} values in the following manner:')
    for firstItems in resultsArchive[:6]: #first 4 items
        print(firstItems)
    print('etc.')
        
br(7, 1)

# 4. MAIN LOOP
for h in range(num_hours):
    print(f"simulation covers {num_hours} hours, now at {int(h)}.")
    print(loadingBar(h+4, num_hours))

    # calc lateral cond without stability explosion
    for step in range(sub_steps):
        print(f"\nmin {step} of {sub_steps} in hour {h}.")
        print(loadingBar(step, sub_steps))
        
        # snapshot of current temps to calc net changes
        T_old = [row[:] for row in T_grid]
        print(f"\nrows: {len(T_old)}.")
        print(f'values per row: {len(T_old[0])}')
        for index, val in enumerate(T_old):
            print(index, val)
        
        for r in range(grid_size):
            for c in range(grid_size):
                flat_idx = r * grid_size + c
                print(f"\nHour: {h}, Sub-step: {step}, Cell: ({r},{c}), Flat index: {flat_idx}")
                T_curr = T_old[r][c]
                
                # fetch hourly irradiance hitting each cell
                print(f"\nFetching solar irradiance for cell index {flat_idx} at hour {h}...")
                I_sol = solar_matrix[flat_idx][h]
                print(f"Solar irradiance I_sol: {I_sol}")
                
                # Boundary Gains & Losses
                q_solar = I_sol * absorptionCoefficient * A_cell
                print(f"Solar heat gain q_solar: {q_solar}")
                q_conv = heatCapacity * A_cell * (T_air - T_curr)
                print(f"Convective heat loss q_conv: {q_conv}")
                q_ground = (thermalConductivity / (thickness * 0.5)) * A_cell * (T_ground - T_curr)
                print(f"Ground heat loss q_ground: {q_ground}")
                
                # Lateral Conduction (Heat moving inside the material itself)
                q_lateral = 0.0
                neighbors = []
                if r > 0: neighbors.append(T_old[r-1][c])             # Up
                if r < grid_size - 1: neighbors.append(T_old[r+1][c]) # Down
                if c > 0: neighbors.append(T_old[r][c-1])             # Left
                if c < grid_size - 1: neighbors.append(T_old[r][c+1]) # Right
                print(f"\nNeighbor temperatures: {neighbors}")
                
                for T_nb in neighbors:
                    q_lateral += (thermalConductivity * (dx * thickness) / dy) * (T_nb - T_curr)
                    print(f"Updated lateral heat transfer q_lateral: {q_lateral}")
                    print(f"Neighbor temperature T_nb: {T_nb}, Current temperature T_curr: {T_curr}")
                
                # Update temperature for the next sub-step
                q_net = q_solar + q_conv + q_ground + q_lateral
                print(f"Net heat transfer q_net: {q_net}")
                T_grid[r][c] += (q_net * dt) / C_cell
                print(f"Updated temperature T_grid[{r}][{c}]: {T_grid[r][c]}")
                
    # At the end of the hour, flatten the 2D grid and archive it
    hourly_flat_temps = []
    for r in range(grid_size):
        for c in range(grid_size):
            hourly_flat_temps.append(T_grid[r][c])
    resultsArchive.append(hourly_flat_temps)
    print(f"Archived temperatures for hour {h}: {hourly_flat_temps}")

# 5. OUTPUT ONLY THE SELECTED HOUR BASED ON THE SLIDER
# Because the loop ran completely upfront, moving the slider updates instantly!
if resultsArchive:
    T_surface = resultsArchive[min(outputHourOfDay, len(resultsArchive) - 1)]
else:
    print("ERROR: resultsArchive is empty — simulation loop failed before first archive")
    T_surface = Noneprint(f"Output temperatures for hour {outputHourOfDay}: {T_surface}")



