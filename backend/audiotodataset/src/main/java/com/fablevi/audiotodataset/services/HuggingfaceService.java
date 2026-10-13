package com.fablevi.audiotodataset.services;

import org.springframework.stereotype.Service;

@Service
public class HuggingfaceService {

    public void createDataset(){
        //TODO:
        //If can! if not show the user how he can do it!

    }

    public void cloneDataset(){
        //If can: somehow ${user.home}/.audiotodataset/dataset/ we need to extract from the folder FE.: dataset/{mydataset}/json....
        //So we delete the {mydataset}
        //Check if it compatible with our dataset structure. If not then do not download it or delete it afterward
        //before we load the dataset in the memory, we need to check if there is a test and validation json. If there is then
        //we need to create 1 memory data from it. then we could delete wav files from it

    }

    public void deleteDataset(){
        //TODO:
        //If can! If not then show the user how he can
    }

    public void pushDataset(){

    }

    private void createTrainTestValidation(){
        //user will set the %, but test and validation will be the same size
    }
}
