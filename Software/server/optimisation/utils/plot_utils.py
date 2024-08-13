# # Plot sun energy, price, inst demand, and deferable demands
# # Create the plot
# fig, axes = plt.subplots(3, 1, figsize=(10, 6), sharex=True)

# # Plot Import / Export
# axes[0].plot(sun_energies, label="Sun Energy", color="orange")
# axes[0].plot(import_prices, label="Import Price", color="blue")
# axes[0].set_title("Sun & Price")
# axes[0].legend()

# # Plot Release / Store
# axes[1].plot(demands, label="Inst Demand", color="orange")
# axes[1].set_title("Instantaneous Demands")
# axes[1].legend()

# # Allocation Demands
# allocations = [dd1_allocations, dd2_allocations, dd3_allocations]
# for i in range(3):
#     dd_energy = [day.deferables[i].energy - sum(allocations[i][:j]) for j in range(60)]
#     axes[2].plot(
#         dd_energy,
#         label=f"DD{i+1} Allocation",
#     )
# axes[2].legend()

# # Add main title
# fig.suptitle("Environment")
# plt.savefig("server/optimisation/bplots/rl_state.png", dpi=500)
# plt.tight_layout(rect=[0, 0.03, 1, 0.95])
# plt.show()

# ACTION PLOT

# # Create the plot
# fig, axes = plt.subplots(3, 1, figsize=(10, 6), sharex=True)

# # Plot Import / Export
# axes[0].plot(import_export, label="Import / Export")
# axes[0].set_title("Import / Export")
# axes[0].legend()

# # Plot Release / Store
# axes[1].plot(release_store, label="Release / Store", color="orange")
# axes[1].set_title("Release / Store")
# axes[1].legend()

# # Allocation Demands
# axes[2].plot(dd1_allocations, label="DD1 Allocation", color="green")
# axes[2].plot(dd2_allocations, label="DD2 Allocation", color="pink")
# axes[2].plot(dd3_allocations, label="DD3 Allocation", color="purple")
# axes[2].legend()

# # Add main title
# fig.suptitle("RL Actions")
# plt.savefig("server/optimisation/bplots/rl_actions.png", dpi=500)
# plt.tight_layout(rect=[0, 0.03, 1, 0.95])
# plt.show()
