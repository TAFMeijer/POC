import sys
try:
    from app import update_chart
    # Test execution
    fig = update_chart('Burkina Faso', 'ALL', 'ALL')
    print("Success!")
except Exception as e:
    import traceback
    traceback.print_exc()
