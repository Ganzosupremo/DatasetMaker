from app_gui import MainApp
import multiprocessing

def main():
    app = MainApp()    
    app.mainloop()
    

if __name__ == "__main__":
    multiprocessing.freeze_support()
    main()
