import time
import thorlabs_TC200

temp_controller = thorlabs_TC200.Controller(
    'COM19', sensor='NTC10K', verbose=True)

print('\n# Testing time required to reach thermal stability:')
temp_controller.set_tset(37)
delay_s = 2
stability_target_s =60
seconds_at_target_temp = []
t0 = time.perf_counter()
temp_controller.set_enable(True)
while True: # this can block forever if the temperature can't be reached...
    if temp_controller.reached_temp(ttol_C=0.2): # are we within 0.2C?
        seconds_at_target_temp.append(delay_s)
    else:
        seconds_at_target_temp = [] # reset list
    if sum(seconds_at_target_temp) == stability_target_s:
        break
    print(' -> waiting to reach temperature (%sC)\n'%temp_controller.tset_C)
    time.sleep(delay_s)
temp_controller.set_enable(False)
t1 = time.perf_counter()
print('\n# Total time to reach thermal stability = %0.2fs'%(t1 - t0))

temp_controller.close()

# Testing a TLK-H flexible foil heater on Nikon 40x0.95 air objective (MRD00405)
# -> starting at tact_C = 22.1 and going to tact_C = 37
# -> 60s of stability with ttol_C=0.2
# -> total time ~ 1971s (~33min)
# -> cooling time from tact_C = 37 to tact_C = 25 (i.e. not fully cooled)
# -> total time ~ 2111s (~35min)
