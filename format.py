import argparse
import pandas as pd
import numpy as np
import os
import re
import json


def get_mouse_coords(trial, idx):
    trial = trial.copy()[trial.trial_type == 'dot-motion-recordCursor']
    x = trial.mouseArrayX.to_numpy().tolist()[idx]
    x = np.array([float(val) for val in x[1:-1].split(',')])
    y = trial.mouseArrayY.to_numpy().tolist()[idx]
    y = np.array([float(val) for val in y[1:-1].split(',')])
    return list(zip(x, y))

def format_trial(trial):
    contr1 = trial.controlLevel1[trial.trial_type == 'dot-motion-recordCursor']
    contr2 = trial.controlLevel2[trial.trial_type == 'dot-motion-recordCursor']
    correct = trial.correct[trial.trial_type == 'dot-motion-recordCursor']
    trial_data = dict(
        control_A1 = contr1.tolist()[0],
        control_A2 = contr2.tolist()[0],
        correct_A = int(correct.tolist()[0]),
        control_B1 = contr1.tolist()[1],
        control_B2 = contr2.tolist()[1],
        correct_B = int(correct.tolist()[1]),
        more_certain = 'A' if trial.iloc[-1].response == '1' else 'B',
        mouse_A = get_mouse_coords(trial, 0),
        mouse_B = get_mouse_coords(trial, 1)
    )
    return trial_data

def main(src, save_dir):
    '''
    Formats the fresh-off-the-jspych data in source directory `src` into
    human-readable tab seperated value files in `save_dir` for long term storage
    '''

    if not os.path.exists(save_dir):
        os.mkdir(save_dir)

    trial_dfs = []
    demographics = []

    # load data
    fs = [os.path.join(src, f) for f in os.listdir(src) if '.csv' in f]
    fs.sort()
    for i in range(len(fs)):
        df = pd.read_csv(fs[i])
        # get indices of paired trials
        idxs_end = df.index[
            df.stimulus.str.contains(
            'About which of the previous two trials were you more certain?'
            ) == True
        ]
        idxs_beg = idxs_end - 4
        trials = [df.iloc[b:e+1] for b, e in zip(idxs_beg, idxs_end)]
        trial_df = pd.DataFrame([format_trial(trial) for trial in trials])
        trial_df.insert(0, 'subject', i)
        trial_dfs.append(trial_df)

        demo = df[df.trial_type == 'survey-multi-choice'].iloc[-1].response
        demo = json.loads(demo)
        demo['subject'] = i
        demographics.append(demo)

    df = pd.concat(trial_dfs)
    demographics = pd.DataFrame(demographics)
    demographics = demographics[['subject', 'sex', 'handedness']]
    df.to_csv(os.path.join(save_dir, 'data.tsv'), sep = '\t', index = False)
    demographics.to_csv(
        os.path.join(save_dir, 'participants.tsv'),
        sep = '\t',
        index = False
        )

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('source_dir', type = str)
    parser.add_argument('save_dir', type = str)
    args = parser.parse_args()
    main(args.source_dir, args.save_dir)
